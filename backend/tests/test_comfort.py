from datetime import date
from uuid import uuid4

from app.db import connect
from app import comfort
from conftest import call, seed, plan


def test_preferences_and_history_only_include_confirmed_meals(client):
    _, recipe, meals = seed(client)
    call(client, 'patch', f'/recipes/{recipe}/preferences', {'favorite': True, 'to_try': True, 'rating': 'a_refaire', 'category': 'vegetarien', 'comment': 'Bon', 'variant': 'Avec des herbes'})
    plan(client, meals[0], recipe)
    assert not call(client, 'get', '/history')['items']
    operation = {'operation_id': str(uuid4())}
    call(client, 'post', f"/meals/{meals[0]['id']}/prepare", operation)
    call(client, 'post', f"/meals/{meals[0]['id']}/prepare", operation)
    history = call(client, 'get', '/history')['items']
    assert len(history) == 1 and history[0]['main_name'] == 'Riz aux légumes'
    assert history[0]['prepared_at'] and history[0]['rating'] == 'a_refaire'
    call(client, 'put', f'/recipes/{recipe}', {'name': 'Nouveau nom', 'kind': 'recette', 'portions': 4})
    assert call(client, 'get', '/history')['items'][0]['main_name'] == 'Riz aux légumes'
    data = call(client, 'get', '/dashboard?start=2026-11-09')
    assert data['recipes'][0]['favorite'] and not data['recipes'][0]['to_try']
    assert data['recipes'][0]['comment'] == 'Bon'


def test_copy_previews_only_empty_home_slots_and_never_consumes(client):
    ingredient, recipe, source = seed(client)
    plan(client, source[0], recipe)
    plan(client, source[1], recipe)
    plan(client, source[2], recipe)
    target = call(client, 'post', '/weeks', {'start': '2026-11-16'})['meals']
    plan(client, target[0], None, status='travail')
    plan(client, target[1], recipe)
    preview = call(client, 'get', '/weeks/2026-11-16/copy-preview?source_start=2026-11-09')
    assert len(preview['items']) == 1 and preview['items'][0]['target_id'] == target[2]['id']
    payload = {'operation_id': str(uuid4()), 'source_start': '2026-11-09', 'preview_token': preview['preview_token']}
    result = call(client, 'post', '/weeks/2026-11-16/copy', payload)
    assert result['copied'] == 1
    assert call(client, 'post', '/weeks/2026-11-16/copy', payload) == result
    current = call(client, 'get', '/weeks/2026-11-16')['meals']
    assert current[0]['status'] == 'travail' and current[1]['recipe_id'] == recipe
    assert current[2]['recipe_id'] == recipe and not current[2]['prepared']
    assert not call(client, 'get', '/history')['items']
    assert not call(client, 'get', '/dashboard?start=2026-11-16')['movements']


def test_copy_stale_preview_refused_and_prepared_meal_can_be_reused(client):
    _, recipe, source = seed(client)
    plan(client, source[0], recipe)
    call(client, 'post', f"/meals/{source[0]['id']}/prepare", {'operation_id': str(uuid4())})
    target = call(client, 'post', '/weeks', {'start': '2026-11-16'})['meals']
    preview = call(client, 'get', '/weeks/2026-11-16/copy-preview?source_start=2026-11-09')
    plan(client, target[0], None, status='exterieur')
    call(client, 'post', '/weeks/2026-11-16/copy', {'operation_id': str(uuid4()), 'source_start': '2026-11-09', 'preview_token': preview['preview_token']}, expected=409)
    body = {'operation_id': str(uuid4()), 'source_meal_id': source[0]['id']}
    first = call(client, 'post', f"/meals/{target[1]['id']}/reuse", body)
    assert call(client, 'post', f"/meals/{target[1]['id']}/reuse", body) == first
    assert not call(client, 'get', '/weeks/2026-11-16')['meals'][1]['prepared']
    assert len(call(client, 'get', '/history')['items']) == 1
    body['operation_id'] = str(uuid4())
    call(client, 'post', f"/meals/{target[1]['id']}/reuse", body, expected=409)


def test_suggestions_are_deterministic_exclude_disliked_and_respect_reservations(client):
    ingredient, recipe, meals = seed(client)
    other = call(client, 'post', '/recipes', {'name': 'Autre idée', 'minutes': 10, 'portions': 4,
        'ingredients': [{'ingredient_id': ingredient, 'quantity': 80, 'unit': 'g'}]})['id']
    disliked = call(client, 'post', '/recipes', {'name': 'Pas pour nous', 'minutes': 5})['id']
    call(client, 'patch', f'/recipes/{disliked}/preferences', {'rating': 'ne_plus_proposer'})
    call(client, 'patch', f'/recipes/{other}/preferences', {'to_try': True, 'category': 'legumes'})
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 100, 'unit': 'g', 'expires': '2026-11-12'})
    query = '/suggestions?day=2026-11-09&mode=stock&portions=4'
    initial = call(client, 'get', query)
    assert initial == call(client, 'get', query)
    assert disliked not in [r['recipe_id'] for r in initial['items']]
    assert any('1/1 ingrédients couverts' in x for x in initial['items'][0]['reasons'])
    plan(client, meals[0], recipe)
    reserved = call(client, 'get', query)
    assert all(any('0/1 ingrédients couverts' in reason for reason in item['reasons']) for item in reserved['items'])
    assert call(client, 'get', '/suggestions?day=2026-11-09&mode=decouverte')['items'][0]['recipe_id'] == other
    assert call(client, 'get', '/suggestions?day=2026-11-09&mode=rapide')['items'][0]['recipe_id'] == other
    assert other not in [r['recipe_id'] for r in call(client, 'get', f'/suggestions?day=2026-11-09&exclude={other}')['items']]


def test_history_cursor_uses_preparation_order_not_meal_creation_order(client):
    _, recipe, meals = seed(client)
    for meal in (meals[4], meals[0]):
        plan(client, meal, recipe)
        call(client, 'post', f"/meals/{meal['id']}/prepare", {'operation_id': str(uuid4())})
    first = call(client, 'get', '/history?limit=1')
    assert first['items'][0]['meal_id'] == meals[0]['id']
    second = call(client, 'get', f"/history?limit=1&before={first['next_before']}")
    assert second['items'][0]['meal_id'] == meals[4]['id']


def test_suggestion_planning_is_idempotent_and_never_overwrites_or_consumes(client):
    _, recipe, meals = seed(client)
    payload = {'operation_id': str(uuid4()), 'recipe_id': recipe}
    path = f"/meals/{meals[0]['id']}/suggestion"
    result = call(client, 'post', path, payload)
    assert call(client, 'post', path, payload) == result
    call(client, 'post', path, {**payload, 'operation_id': str(uuid4())}, expected=409)
    plan(client, meals[1], None, status='travail')
    call(client, 'post', f"/meals/{meals[1]['id']}/suggestion", {**payload, 'operation_id': str(uuid4())}, expected=409)
    data = call(client, 'get', '/dashboard?start=2026-11-09')
    assert not data['movements'] and not call(client, 'get', '/history')['items']


def test_phase_b_migration_preserves_old_preparations_without_inventing_dates(tmp_path):
    import sqlite3
    from pathlib import Path
    from alembic import command
    from alembic.config import Config
    from app.db import migrate

    database = tmp_path / 'legacy.sqlite3'
    backend = Path(__file__).resolve().parents[1]
    config = Config(str(backend / 'alembic.ini'))
    config.set_main_option('script_location', str(backend / 'migrations'))
    config.set_main_option('sqlalchemy.url', 'sqlite:///' + str(database))
    command.upgrade(config, '0002')
    with sqlite3.connect(database) as db:
        db.execute("INSERT INTO recipes (id,name,kind,portions,source_author) VALUES (1,'Soupe témoin','recette',4,'Auteur fictif')")
        db.execute("INSERT INTO weeks VALUES ('2026-11-09')")
        db.execute("INSERT INTO meals (week_start,day,slot,status,recipe_id,portions,prepared) VALUES ('2026-11-09','2026-11-09','soir','maison',1,4,1)")
        db.execute("INSERT INTO ingredients VALUES (1,'Riz','masse')")
        db.execute("INSERT INTO stock VALUES (1,1,'Placard',125000,NULL)")
    migrate(database)
    migrate(database)
    with sqlite3.connect(database) as db:
        assert db.execute('SELECT main_name,prepared_at FROM meal_history').fetchall() == [('Soupe témoin', None)]
        assert db.execute('SELECT favorite,to_try,comment,source_author FROM recipes').fetchone() == (0,0,'','Auteur fictif')
        assert db.execute('SELECT quantity FROM stock').fetchone()[0] == 125000
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
