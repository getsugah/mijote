import base64
from io import BytesIO
from pathlib import Path
import sqlite3
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from PIL import Image

from app.backup import backup, restore
from app.db import migrate
from app.main import create_app
from conftest import call


def recipes(client):
    call(client, 'post', '/weeks', {'start': '2026-11-09'})
    return call(client, 'get', '/dashboard?start=2026-11-09')['recipes']


def dump(path):
    with sqlite3.connect(f'file:{path}?mode=ro', uri=True) as db:
        return '\n'.join(db.iterdump())


def photo():
    stream = BytesIO()
    Image.new('RGB', (16, 12), 'orange').save(stream, 'JPEG')
    return {'data_base64': base64.b64encode(stream.getvalue()).decode(), 'source_url': '', 'attribution': 'Image fictive'}


def test_advice_is_read_only_and_does_not_claim_dietary_safety(client, tmp_path):
    before = dump(tmp_path / 'mijote.sqlite3')
    result = call(client, 'post', '/recipes/advice', {'name': '  SOUPE   AU POULET ', 'ingredients': ['Tomates', 'Pommes de terre'], 'minutes': 25})
    assert result['title'] == 'Soupe au poulet'
    names = {t['name'] for t in result['tags']}
    assert {'Poulet', 'Tomates', 'Pommes de terre', 'Soupe', 'Rapide'} <= names
    assert not {'Végétarien', 'Sans gluten', 'Sans allergènes'} & names
    assert 'Aucune garantie' in result['message']
    assert dump(tmp_path / 'mijote.sqlite3') == before
    empty = call(client, 'post', '/recipes/advice', {})
    assert empty['title'] == '' and empty['tags'] == []
    generated = call(client, 'post', '/recipes/advice', {'ingredients': ['Riz', 'Courgettes']})
    assert generated['title'] == 'Recette : Riz, Courgettes'


def test_only_chosen_title_tags_and_photo_are_saved_and_old_edits_preserve_them(client):
    advice = call(client, 'post', '/recipes/advice', {'name': 'SOUPE AUX TOMATES', 'ingredients': ['Tomates'], 'minutes': 15})
    saved = call(client, 'post', '/recipes', {'name': 'Mon titre validé', 'kind': 'simple', 'tags': ['  Famille  ', 'FAMILLE', 'À refaire'], 'photo': photo()})
    entry = recipes(client)[0]
    assert entry['id'] == saved['id'] and entry['name'] == 'Mon titre validé'
    assert set(entry['tags']) == {'Famille', 'À refaire'}
    assert entry['photo_version']
    assert 'Rapide' not in entry['tags'] and entry['name'] != advice['title']
    call(client, 'put', f"/recipes/{saved['id']}", {'name': 'Titre corrigé', 'kind': 'simple'})
    edited = recipes(client)[0]
    assert edited['tags'] == entry['tags'] and edited['photo_version'] == entry['photo_version']
    call(client, 'put', f"/recipes/{saved['id']}", {'name': 'Titre corrigé', 'kind': 'simple', 'tags': []})
    assert recipes(client)[0]['tags'] == []
    assert recipes(client)[0]['photo_version'] == entry['photo_version']


def test_invalid_tag_or_photo_keeps_recipe_and_tags_atomic(client, tmp_path):
    saved = call(client, 'post', '/recipes', {'name': 'Soupe fictive', 'kind': 'simple', 'tags': ['Maison'], 'photo': photo()})['id']
    before = dump(tmp_path / 'mijote.sqlite3')
    for body in [ {'tags': ['   ']}, {'tags': ['x' * 51]}, {'tags': [str(i) for i in range(21)]}, {'tags': ['Autre'], 'photo': {'data_base64': 'incorrect'} } ]:
        call(client, 'put', f'/recipes/{saved}', {'name': 'Nom à ne pas appliquer', 'kind': 'simple', **body}, expected=422)
        assert dump(tmp_path / 'mijote.sqlite3') == before


def test_tags_are_canonical_shared_and_deleted_links_do_not_damage_other_recipes(client):
    first = call(client, 'post', '/recipes', {'name': 'Soupe fictive', 'kind': 'simple', 'tags': ['Famille']})['id']
    second = call(client, 'post', '/recipes', {'name': 'Gratin fictif', 'kind': 'simple', 'tags': ['FAMILLE']})['id']
    assert all(r['tags'] == ['Famille'] for r in recipes(client))
    call(client, 'delete', f'/recipes/{first}')
    assert recipes(client)[0]['id'] == second and recipes(client)[0]['tags'] == ['Famille']


def test_import_confirm_saves_only_chosen_tags_and_is_idempotent(client):
    body = {'operation_id': str(uuid4()), 'recipe': {'name': 'Import fictif', 'tags': ['À tester']}, 'items': [], 'photo': photo()}
    first = call(client, 'post', '/recipes/import/confirm', body)
    assert call(client, 'post', '/recipes/import/confirm', body) == first
    assert len(recipes(client)) == 1
    assert recipes(client)[0]['tags'] == ['À tester']
    assert recipes(client)[0]['photo_version']


def test_migration_adds_empty_tags_without_changing_existing_rows_and_backup_keeps_tags(tmp_path):
    path = tmp_path / 'legacy.sqlite3'
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / 'alembic.ini'))
    config.set_main_option('script_location', str(root / 'migrations'))
    config.set_main_option('sqlalchemy.url', 'sqlite:///' + str(path))
    command.upgrade(config, '0008')
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO recipes(id,name,kind,portions,steps) VALUES(7,'Recette témoin','simple',4,'Étapes conservées')")
        db.execute("INSERT INTO ingredients(id,name,dimension) VALUES(3,'Riz fictif','masse')")
        db.execute("INSERT INTO stock(id,ingredient_id,location,quantity,label) VALUES(8,3,'Placard',42000,'Bocal fictif')")
        db.execute("INSERT INTO movements(ingredient_id,stock_id,delta,reason) VALUES(3,8,42000,'Entrée fictive')")
        before = {table: db.execute(f'SELECT * FROM {table}').fetchall() for table in ('recipes','stock','movements')}
    migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT COUNT(*) FROM recipe_tags').fetchone()[0] == 0
        for table in before:
            assert db.execute(f'SELECT * FROM {table}').fetchall() == before[table]
    with TestClient(create_app(path, secure_cookie=False)) as client:
        session = call(client, 'post', '/auth/setup', {'name': 'Maison fictive', 'password': 'Mot-de-passe-fictif-123'})
        client.headers['X-CSRF-Token'] = session['csrf']
        call(client, 'put', '/recipes/7', {'name': 'Recette témoin', 'kind': 'simple', 'tags': ['Maison'], 'photo': photo()})
        saved = tmp_path / 'snapshot.sqlite3'
        backup(path, saved)
    restore(saved, path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT name FROM tags').fetchall() == [('Maison',)]
        assert db.execute('SELECT recipe_id FROM recipe_tags').fetchall() == [(7,)]
        assert db.execute('SELECT COUNT(*) FROM recipe_photos').fetchone()[0] == 1
        assert not db.execute('PRAGMA foreign_key_check').fetchall()


def test_advice_requires_authentication_and_csrf(client):
    token = client.headers.pop('X-CSRF-Token')
    call(client, 'post', '/recipes/advice', {}, expected=403)
    client.headers['X-CSRF-Token'] = token
    call(client, 'post', '/auth/logout')
    call(client, 'post', '/recipes/advice', {}, expected=401)
