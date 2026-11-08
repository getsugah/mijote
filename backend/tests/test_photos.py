import base64
from io import BytesIO
import json
import sqlite3
import time
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image
from app import photos, recipe_import, safe_fetch
from app.backup import backup, restore
from app.main import create_app
from conftest import call, seed


def image_bytes(fmt='JPEG', size=(200,100), color='orange', **save):
    stream = BytesIO()
    Image.new('RGB', size, color).save(stream, fmt, **save)
    return stream.getvalue()


@pytest.mark.parametrize('fmt', ['JPEG','PNG','WEBP'])
def test_supported_photos_are_bounded_jpegs_without_metadata(fmt):
    result = photos.normalize(image_bytes(fmt, size=(1800,900)))
    assert result['width'] == 1600 and result['height'] == 800
    assert len(result['data']) <= photos.MAX_OUTPUT
    with Image.open(BytesIO(result['data'])) as decoded:
        assert decoded.format == 'JPEG' and decoded.mode == 'RGB'
        assert not decoded.getexif() and not decoded.info.get('icc_profile')


def test_orientation_corrected_and_exif_gps_comment_removed():
    exif = Image.Exif(); exif[274] = 6; exif[270] = 'Description fictive'; exif[315] = 'Auteur fictif'
    result = photos.normalize(image_bytes(exif=exif, comment=b'Commentaire fictif'))
    assert (result['width'],result['height']) == (100,200)
    with Image.open(BytesIO(result['data'])) as decoded:
        assert not decoded.getexif() and not decoded.info.get('comment')


@pytest.mark.parametrize('raw', [b'<svg><script>test</script></svg>', b'not an image', image_bytes()[:30]])
def test_invalid_active_or_truncated_images_are_refused(raw):
    with pytest.raises(HTTPException) as error: photos.normalize(raw)
    assert error.value.status_code == 422


def test_size_pixels_and_animation_limits(monkeypatch):
    with pytest.raises(HTTPException) as error: photos.normalize(b'a'*(photos.MAX_UPLOAD+1))
    assert error.value.status_code == 413
    monkeypatch.setattr(photos, 'MAX_PIXELS', 10)
    with pytest.raises(HTTPException, match='24 mégapixels'): photos.normalize(image_bytes())
    monkeypatch.setattr(photos, 'MAX_PIXELS', 24_000_000)
    stream=BytesIO(); first=Image.new('RGB',(10,10),'red'); first.save(stream,'WEBP',save_all=True,append_images=[Image.new('RGB',(10,10),'blue')],duration=100)
    with pytest.raises(HTTPException, match='sans animation'): photos.normalize(stream.getvalue())


def upload(client, recipe, raw):
    return client.put(f'/api/v1/recipes/{recipe}/photo', content=raw, headers={'Content-Type':'image/jpeg'})


def test_manual_upload_replace_remove_and_private_delivery(client):
    _, recipe, _ = seed(client)
    first = upload(client, recipe, image_bytes())
    assert first.status_code == 200
    picture = client.get(f'/api/v1/recipes/{recipe}/photo')
    assert picture.status_code == 200 and picture.headers['content-type']=='image/jpeg'
    assert picture.headers['cache-control']=='no-store'
    second = upload(client, recipe, image_bytes(color='blue'))
    assert second.json()['photo_version'] != first.json()['photo_version']
    before = call(client,'get','/dashboard?start=2026-11-09')
    assert before['recipes'][0]['photo_version']==second.json()['photo_version']
    assert 'data' not in before['recipes'][0] and not before['movements'] and not before['stock']
    csrf = client.headers.pop('X-CSRF-Token')
    assert upload(client,recipe,image_bytes()).status_code == 403
    client.headers['X-CSRF-Token']=csrf
    call(client,'delete',f'/recipes/{recipe}/photo')
    assert client.get(f'/api/v1/recipes/{recipe}/photo').status_code==404
    upload(client,recipe,image_bytes())
    call(client,'post','/auth/logout')
    assert client.get(f'/api/v1/recipes/{recipe}/photo').status_code==401
    assert upload(client,recipe,image_bytes()).status_code==401


def test_invalid_replacement_keeps_existing_photo_and_chunked_upload_is_bounded(client):
    _,recipe,_=seed(client)
    original=upload(client,recipe,image_bytes()).json()['photo_version']
    assert upload(client,recipe,b'bad').status_code==422
    assert call(client,'get','/dashboard?start=2026-11-09')['recipes'][0]['photo_version']==original
    response=client.put(f'/api/v1/recipes/{recipe}/photo',content=(b'a'*1024*1024 for _ in range(13)),headers={'Content-Type':'image/jpeg'})
    assert response.status_code==413


def draft(raw=None):
    return {'data_base64':base64.b64encode(raw or image_bytes()).decode(), 'source_url':'https://images.example/soupe.jpg','attribution':'Atelier fictif'}


def confirmation(photo):
    return {'operation_id':str(uuid4()),'recipe':{'name':'Photo témoin','kind':'recette','portions':4},'items':[{'name':'Riz témoin','quantity':100,'unit':'g'}],'photo':photo}


def test_import_photo_is_atomic_idempotent_and_keeps_source(client):
    call(client,'post','/weeks',{'start':'2026-11-09'})
    body=confirmation(draft())
    result=call(client,'post','/recipes/import/confirm',body)
    assert call(client,'post','/recipes/import/confirm',body)==result
    value=call(client,'get','/dashboard?start=2026-11-09')
    recipe=value['recipes'][0]
    assert len(value['recipes'])==1 and recipe['photo_source']=='https://images.example/soupe.jpg'
    assert recipe['photo_attribution']=='Atelier fictif' and not value['movements']
    body=confirmation(draft(b'not an image'));body['items'][0]['name']='Autre témoin'
    call(client,'post','/recipes/import/confirm',body,expected=422)
    after=call(client,'get','/dashboard?start=2026-11-09')
    assert len(after['recipes'])==1 and len(after['ingredients'])==1


def test_remote_photo_preview_has_no_writes_and_uses_safe_fetch(client,monkeypatch):
    call(client,'post','/weeks',{'start':'2026-11-09'})
    monkeypatch.setattr(safe_fetch,'fetch_image',lambda url:(image_bytes(),url))
    value=call(client,'post','/recipes/import/photo/preview',{'url':'https://images.example/a.jpg','attribution':'Atelier fictif'})
    assert value['width']==200 and value['data_base64']
    data=call(client,'get','/dashboard?start=2026-11-09')
    assert not data['recipes'] and not data['ingredients']
    monkeypatch.setattr(safe_fetch,'fetch_image',lambda url:(_ for _ in ()).throw(safe_fetch.ImportProblem('Photo refusée')))
    call(client,'post','/recipes/import/photo/preview',{'url':'https://images.example/b.jpg'},expected=422)


def test_extracts_relative_image_and_credit_without_downloading():
    document={'@type':'Recipe','name':'Soupe témoin','recipeIngredient':['200 g de riz'],'image':{'@type':'ImageObject','contentUrl':'/images/soupe.jpg','author':{'name':'Atelier fictif'}}}
    parsed=recipe_import.parse_html('<script type="application/ld+json">'+json.dumps(document)+'</script>','https://recettes.example/soupe')
    assert parsed['image_url']=='https://recettes.example/images/soupe.jpg' and parsed['image_author']=='Atelier fictif'
    html='<meta property="og:image" content="/photo.png"><h1>Soupe</h1><h2>Ingrédients</h2><ul><li>200 g de riz</li></ul><h2>Préparation</h2><p>Cuire</p>'
    assert recipe_import.parse_html(html,'https://recettes.example/a')['image_url']=='https://recettes.example/photo.png'
    assert not recipe_import.image_info('javascript:alert(1)','https://recettes.example/a')[0]


def test_image_fetch_revalidates_redirects_to_private_network(monkeypatch):
    monkeypatch.setattr(safe_fetch,'resolve_public',lambda *a:['93.184.216.34'])
    calls=[]
    def redirect(target,addresses,deadline,image=False):
        assert image;calls.append(target.url);return 302,'http://localhost/photo',None
    monkeypatch.setattr(safe_fetch,'request_once',redirect)
    with pytest.raises(safe_fetch.ImportProblem): safe_fetch.fetch_image('https://images.example/photo')
    assert len(calls)==1


def test_photos_survive_backup_restore_and_recipe_deletion_cascades(tmp_path):
    path=tmp_path/'mijote.sqlite3';saved=tmp_path/'saved.sqlite3'
    with TestClient(create_app(path,secure_cookie=False)) as client:
        session=call(client,'post','/auth/setup',{'name':'Maison témoin','password':'Mot-de-passe-fictif-123'})
        client.headers['X-CSRF-Token']=session['csrf']
        _,recipe,_=seed(client);upload(client,recipe,image_bytes());backup(path,saved)
        call(client,'delete',f'/recipes/{recipe}')
        with sqlite3.connect(path) as db: assert db.execute('SELECT count(*) FROM recipe_photos').fetchone()[0]==0
    restore(saved,path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT length(data) FROM recipe_photos').fetchone()[0]>0
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        assert db.execute('SELECT version_num FROM alembic_version').fetchone()[0]=='0004'
