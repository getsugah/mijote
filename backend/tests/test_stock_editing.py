from uuid import uuid4
from alembic import command
from alembic.config import Config
from pathlib import Path

from app.db import connect, migrate
from conftest import call, seed, plan


def dashboard(client):
    return call(client, 'get', '/dashboard?start=2026-11-09')


def test_edit_lot_preserves_catalogue_and_records_changes(client):
    ident, _, _ = seed(client)
    lot = call(client, 'post', '/stock', {'ingredient_id': ident, 'quantity': 500, 'unit': 'g', 'expires': '2027-01-01'})['id']
    call(client, 'patch', f'/stock/{lot}', {'name': 'Riz du bocal', 'quantity': 0.25, 'unit': 'kg', 'location': 'Cellier', 'expires': None, 'reason': 'Inventaire'})
    data = dashboard(client)
    assert data['stock'][0]['id'] == lot
    assert data['stock'][0]['name'] == 'Riz du bocal'
    assert data['stock'][0]['quantity'] == 250
    assert data['stock'][0]['location'] == 'Cellier'
    assert data['stock'][0]['expires'] is None
    assert data['ingredients'][0]['name'] == 'Riz basmati'
    assert data['recipes'][0]['ingredients'][0]['ingredient_id'] == ident
    assert data['movements'][0]['delta'] == -250
    assert 'Cellier' in data['movements'][0]['reason']
    call(client, 'patch', f'/stock/{lot}', {'quantity': 100, 'unit': 'g', 'reason': 'Ancien client'})
    current = dashboard(client)['stock'][0]
    assert (current['name'], current['location'], current['quantity']) == ('Riz du bocal', 'Cellier', 100)


def test_locations_are_saved_even_empty_and_reused_without_case_duplicates(client):
    seed(client)
    assert call(client, 'post', '/locations', {'name': '  Tiroir   haut  '})['name'] == 'Tiroir haut'
    assert call(client, 'post', '/locations', {'name': 'TIROIR HAUT'})['name'] == 'Tiroir haut'
    assert call(client, 'post', '/locations', {'name': 'RÉFRIGÉRATEUR'})['name'] == 'Réfrigérateur'
    values = call(client, 'get', '/locations')
    assert len(values) == 4
    assert 'Tiroir haut' in dashboard(client)['locations']
    call(client, 'post', '/locations', {'name': '   '}, expected=422)


def test_invalid_edit_is_atomic_and_keeps_original_lot(client):
    ident, _, _ = seed(client)
    lot = call(client, 'post', '/stock', {'ingredient_id': ident, 'quantity': 100, 'unit': 'g'})['id']
    before = dashboard(client)
    for edit in [{'name': '  '}, {'quantity': -1}, {'unit': 'l'}, {'location': '  '}]:
        call(client, 'patch', f'/stock/{lot}', {'name': 'Autre nom', 'quantity': 50, 'unit': 'g', 'location': 'Nouveau lieu', 'reason': 'Correction', **edit}, expected=422)
    after = dashboard(client)
    assert after['stock'] == before['stock']
    assert after['movements'] == before['movements']
    assert after['locations'] == before['locations']


def test_edit_does_not_break_cancellation_of_a_prepared_meal(client):
    ident, recipe, meals = seed(client, quantity=40)
    lot = call(client, 'post', '/stock', {'ingredient_id': ident, 'quantity': 100, 'unit': 'g'})['id']
    plan(client, meals[0], recipe)
    operation = str(uuid4())
    call(client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': operation})
    call(client, 'patch', f'/stock/{lot}', {'name': 'Riz en boîte', 'quantity': 60, 'unit': 'g', 'location': 'Cellier', 'reason': 'Rangement'})
    call(client, 'post', f"/meals/{meals[0]['id']}/unprepare", {'operation_id': str(uuid4()), 'preparation_id': operation})
    item = dashboard(client)['stock'][0]
    assert item['quantity'] == 100 and item['name'] == 'Riz en boîte' and item['location'] == 'Cellier'


def test_migration_keeps_existing_quantities_ids_and_journal(tmp_path):
    path = tmp_path / 'migration.sqlite3'
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / 'alembic.ini'))
    config.set_main_option('script_location', str(root / 'migrations'))
    config.set_main_option('sqlalchemy.url', 'sqlite:///' + str(path))
    command.upgrade(config, '0007')
    with connect(path) as db:
        db.execute("INSERT INTO ingredients(id,name,dimension) VALUES (1,'Riz de test','masse')")
        db.execute("INSERT INTO stock(id,ingredient_id,location,quantity) VALUES (7,1,'  Cellier  ',42000)")
        db.execute("INSERT INTO movements(ingredient_id,stock_id,delta,reason) VALUES (1,7,42000,'Entrée de test')")
    migrate(path)
    with connect(path) as db:
        lot = dict(db.execute('SELECT * FROM stock WHERE id=7').fetchone())
        assert lot['quantity'] == 42000 and lot['label'] == '' and lot['location'] == 'Cellier'
        assert db.execute('SELECT delta FROM movements WHERE stock_id=7').fetchone()[0] == 42000
        assert db.execute("SELECT COUNT(*) FROM stock_locations WHERE name='Cellier'").fetchone()[0] == 1


def test_old_edit_cannot_restore_quantity_consumed_since_opening(client):
    ident, recipe, meals = seed(client, quantity=40)
    lot = call(client, 'post', '/stock', {'ingredient_id': ident, 'quantity': 100, 'unit': 'g'})['id']
    opened = dashboard(client)['stock'][0]
    plan(client, meals[0], recipe)
    call(client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': str(uuid4())})
    call(client, 'patch', f'/stock/{lot}', {'version': opened['version'], 'quantity': 100, 'unit': 'g', 'name': 'Riz du bocal', 'reason': 'Renommage'}, expected=409)
    assert dashboard(client)['stock'][0]['quantity'] == 60


def test_backup_keeps_custom_names_and_empty_locations(tmp_path):
    import sqlite3
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.backup import backup, restore
    path, saved = tmp_path / 'house.sqlite3', tmp_path / 'snapshot.sqlite3'
    with TestClient(create_app(path, secure_cookie=False)) as client:
        session = call(client, 'post', '/auth/setup', {'name': 'Maison témoin', 'password': 'Mot-de-passe-fictif-123'})
        client.headers['X-CSRF-Token'] = session['csrf']
        ident, _, _ = seed(client)
        call(client, 'post', '/locations', {'name': 'Étagère de test'})
        lot = call(client, 'post', '/stock', {'ingredient_id': ident, 'quantity': 100, 'unit': 'g'})['id']
        call(client, 'patch', f'/stock/{lot}', {'name': 'Bocal de test', 'quantity': 75, 'unit': 'g', 'location': 'Cellier', 'reason': 'Inventaire'})
        backup(path, saved)
    restore(saved, path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT label,quantity,location FROM stock WHERE id=?', (lot,)).fetchone() == ('Bocal de test', 75000, 'Cellier')
        assert db.execute("SELECT COUNT(*) FROM stock_locations WHERE name='Étagère de test'").fetchone()[0] == 1
        assert not db.execute('PRAGMA foreign_key_check').fetchall()


def test_rename_and_delete_location_transfer_lots_and_keep_history(client):
    ident, _, _ = seed(client)
    lot = call(client, 'post', '/stock', {'ingredient_id': ident, 'quantity': 100, 'unit': 'g'})['id']
    before = dashboard(client)
    call(client, 'patch', '/locations/Placard', {'name': '  Garde   manger '})
    renamed = dashboard(client)
    assert renamed['stock'][0]['location'] == 'Garde manger'
    assert renamed['stock'][0]['version'] != before['stock'][0]['version']
    assert 'Placard' not in renamed['locations']
    call(client, 'delete', '/locations/Garde%20manger', {'name': 'Réfrigérateur'})
    after = dashboard(client)
    assert after['stock'][0]['id'] == lot
    assert after['stock'][0]['quantity'] == 100
    assert after['stock'][0]['location'] == 'Réfrigérateur'
    assert after['movements'] == before['movements']
    assert 'Garde manger' not in after['locations']


def test_location_conflicts_and_invalid_deletions_are_atomic(client):
    seed(client)
    before = dashboard(client)
    call(client, 'patch', '/locations/Placard', {'name': 'RÉFRIGÉRATEUR'}, expected=409)
    call(client, 'patch', '/locations/Placard', {'name': '   '}, expected=422)
    call(client, 'delete', '/locations/Placard', {'name': 'Placard'}, expected=422)
    call(client, 'delete', '/locations/Placard', {'name': 'Inconnu'}, expected=422)
    call(client, 'patch', '/locations/Inconnu', {'name': 'Autre'}, expected=404)
    assert dashboard(client)['locations'] == before['locations']
    call(client, 'patch', '/locations/Placard', {'name': 'PLACARD'})
    assert 'PLACARD' in dashboard(client)['locations']
