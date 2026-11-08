"""Exercise recipe photos on a fresh isolated instance; never touches an existing home."""
import base64
import http.cookiejar
from io import BytesIO
import json
import secrets
import sys
from urllib.parse import urlsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener
from urllib.error import HTTPError
from uuid import uuid4
from PIL import Image


def main():
    base=sys.argv[1].rstrip('/')
    target=urlsplit(base)
    if target.scheme!='http' or target.hostname!='127.0.0.1' or not target.port or target.port==8080 or target.path:
        raise SystemExit('Utiliser une instance isolée sur loopback et un port distinct.')
    opener=build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()));csrf=''
    def call(path,method='GET',body=None,raw=None,expected=200):
        request=Request(base+'/api/v1'+path,method=method,headers={'Content-Type':'image/png' if raw is not None else 'application/json','X-CSRF-Token':csrf},data=raw if raw is not None else json.dumps(body or {}).encode() if method!='GET' else None)
        try:
            with opener.open(request,timeout=40) as response: status,content,mime=response.status,response.read(),response.headers.get_content_type()
        except HTTPError as error: status,content,mime=error.code,error.read(),'application/json'
        assert status==expected,(path,status,content[:200])
        return content if mime=='image/jpeg' else json.loads(content)
    assert not call('/auth/status')['initialized'],'Ne pas utiliser une maison existante.'
    session=call('/auth/setup','POST',{'name':'Maison de validation photo','password':secrets.token_urlsafe(32)});csrf=session['csrf']
    call('/weeks','POST',{'start':'2026-11-09'})
    recipe=call('/recipes','POST',{'name':'Soupe témoin','kind':'recette','portions':4})['id']
    source=BytesIO();image=Image.new('RGB',(2400,1200),'orange');exif=Image.Exif();exif[315]='Atelier fictif';image.save(source,'PNG',exif=exif)
    first=call(f'/recipes/{recipe}/photo','PUT',raw=source.getvalue())
    jpeg=call(f'/recipes/{recipe}/photo')
    with Image.open(BytesIO(jpeg)) as decoded:
        assert decoded.format=='JPEG' and decoded.size==(1600,800) and not decoded.getexif()
    data=call('/dashboard?start=2026-11-09');assert data['recipes'][0]['photo_version']==first['photo_version'] and not data['movements']
    photo={'data_base64':base64.b64encode(jpeg).decode(),'source_url':'https://images.example/soupe.jpg','attribution':'Atelier fictif'}
    body={'operation_id':str(uuid4()),'recipe':{'name':'Recette photo importée témoin','kind':'recette','portions':4},'items':[],'photo':photo}
    imported=call('/recipes/import/confirm','POST',body)
    assert call('/recipes/import/confirm','POST',body)==imported
    assert call(f"/recipes/{imported['id']}/photo")
    call(f'/recipes/{recipe}/photo','DELETE');call(f'/recipes/{recipe}/photo',expected=404)
    if '--public' in sys.argv:
        page=call('/recipes/import/preview','POST',{'mode':'url','url':'https://www.marmiton.org/recettes/recette_soupe-de-legumes_222646.aspx','text':''})
        assert page['image_url'],'Aucune photo proposée sur la page publique testée.'
        remote=call('/recipes/import/photo/preview','POST',{'url':page['image_url'],'attribution':page['image_author']})
        assert remote['data_base64'] and remote['width']<=1600 and remote['height']<=1600
        print('Photo publique proposée et téléchargée par le serveur ; aucun texte ni photo de ce site enregistré comme recette.')
    print('Photos HTTP : téléversement, réduction, retrait des métadonnées, affichage privé, import atomique et suppression validés sur données synthétiques.')


if __name__=='__main__':
    main()
