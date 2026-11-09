from uuid import uuid4

from app.backup import backup, restore
from app.db import connect
from conftest import call, seed, plan


def dashboard(client, start='2026-11-09'):
    return call(client, 'get', '/dashboard?start=' + start)


def update(client, meal, **parts):
    return call(client, 'put', f"/meals/{meal['id']}", {'status': 'maison', 'portions': 4, **parts})


def test_multiple_recipes_and_ingredient_side_sum_with_portions_and_units(client):
    ingredient, first, meals = seed(client, quantity=200, portions=4)
    second = call(client, 'post', '/recipes', {'name': 'Deuxième plat fictif', 'portions': 2,
        'ingredients': [{'ingredient_id': ingredient, 'quantity': 100, 'unit': 'g'}]})['id']
    update(client, meals[0], recipe_id=first, portions=6,
           side_ingredient={'ingredient_id': ingredient, 'quantity': 0.5, 'unit': 'kg'},
           dishes=[{'recipe_id': second}, {'ingredient_id': ingredient, 'quantity': 100, 'unit': 'g'}, {'title': 'Salade sans quantités'}])
    data = dashboard(client)
    assert data['shopping']['items'][0]['quantity'] == 1200  # 300 + 300 + 500 + 100
    meal = data['week']['meals'][0]
    assert len(meal['dishes']) == 3
    assert meal['side_ingredient']['quantity'] == 500 and meal['side_ingredient']['unit'] == 'g'
    assert '500 g' in meal['side_name']
    assert not data['stock'] and not data['movements']
    update(client, meals[2], recipe_id=first, portions=6, side_ingredient=meal['side_ingredient'],
           dishes=[{'recipe_id': second}, {'ingredient_id': ingredient, 'quantity': 100, 'unit': 'g'}])
    assert dashboard(client)['shopping']['items'][0]['quantity'] == 2400


def test_prepare_and_undo_include_all_items_and_preserve_history_names(client):
    ingredient, recipe, meals = seed(client)
    update(client, meals[0], recipe_id=recipe, side_ingredient={'ingredient_id': ingredient, 'quantity': 50, 'unit': 'g'},
           dishes=[{'ingredient_id': ingredient, 'quantity': 25, 'unit': 'g'}, {'title': 'Plat ajouté fictif'}])
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 200, 'unit': 'g'})
    operation = str(uuid4())
    prepared = call(client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': operation})
    assert not prepared['shortages']
    assert dashboard(client)['stock'][0]['quantity'] == 25
    event = call(client, 'get', '/history')['items'][0]
    assert len(event['dishes']) == 2 and event['dishes'][1]['name'] == 'Plat ajouté fictif'
    assert '50 g' in event['side_name']
    call(client, 'put', f'/ingredients/{ingredient}', {'name': 'Nom corrigé fictif', 'dimension': 'masse'})
    assert call(client, 'get', '/history')['items'][0]['dishes'][0]['name'] == event['dishes'][0]['name']
    call(client, 'put', f"/meals/{meals[0]['id']}", {'status': 'maison', 'portions': 4, 'dishes': []}, expected=409)
    call(client, 'post', f"/meals/{meals[0]['id']}/unprepare", {'operation_id': str(uuid4()), 'preparation_id': operation})
    assert dashboard(client)['stock'][0]['quantity'] == 200
    assert not call(client, 'get', '/history')['items']


def test_only_added_recipe_or_ingredient_is_a_valid_meal(client):
    ingredient, recipe, meals = seed(client)
    update(client, meals[0], dishes=[{'recipe_id': recipe}])
    update(client, meals[2], side_ingredient={'ingredient_id': ingredient, 'quantity': 40, 'unit': 'g'})
    assert dashboard(client)['shopping']['items'][0]['quantity'] == 140
    call(client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': str(uuid4())})
    call(client, 'post', f"/meals/{meals[2]['id']}/prepare", {'operation_id': str(uuid4())})
    assert not dashboard(client)['shopping']['items']
    assert len(call(client, 'get', '/history')['items']) == 2


def test_away_meal_excludes_every_part_and_can_be_restored(client):
    ingredient, _, meals = seed(client)
    update(client, meals[0], dishes=[{'ingredient_id': ingredient, 'quantity': 200, 'unit': 'g'}])
    update(client, meals[0], status='travail')  # older clients must preserve unknown parts
    assert not dashboard(client)['shopping']['items']
    assert len(dashboard(client)['week']['meals'][0]['dishes']) == 1
    update(client, meals[0])
    assert dashboard(client)['shopping']['items'][0]['quantity'] == 200


def test_copy_and_reuse_keep_all_parts_and_do_not_overwrite_side_only_targets(client):
    ingredient, recipe, meals = seed(client)
    update(client, meals[0], recipe_id=recipe, side_ingredient={'ingredient_id': ingredient, 'quantity': 50, 'unit': 'g'}, dishes=[{'recipe_id': recipe}, {'title': 'Dessert fictif'}])
    target = call(client, 'post', '/weeks', {'start': '2026-11-16'})['meals']
    update(client, target[0], side_ingredient={'ingredient_id': ingredient, 'quantity': 10, 'unit': 'g'})
    preview = call(client, 'get', '/weeks/2026-11-16/copy-preview?source_start=2026-11-09')
    assert not preview['items']
    call(client, 'post', f"/meals/{target[0]['id']}/reuse", {'operation_id': str(uuid4()), 'source_meal_id': meals[0]['id']}, expected=409)
    call(client, 'post', f"/meals/{target[1]['id']}/reuse", {'operation_id': str(uuid4()), 'source_meal_id': meals[0]['id']})
    data = dashboard(client, '2026-11-16')
    assert len(data['week']['meals'][1]['dishes']) == 2
    assert data['week']['meals'][1]['side_ingredient']['quantity'] == 50
    assert data['shopping']['items'][0]['quantity'] == 260
    assert not data['stock']
    update(client, target[0], side_ingredient=None)
    preview = call(client, 'get', '/weeks/2026-11-16/copy-preview?source_start=2026-11-09')
    copied = call(client, 'post', '/weeks/2026-11-16/copy', {'operation_id': str(uuid4()), 'source_start': '2026-11-09', 'preview_token': preview['preview_token']})
    assert copied['copied'] == 1
    assert len(dashboard(client, '2026-11-16')['week']['meals'][0]['dishes']) == 2


def test_extras_protect_template_and_suggestions_and_support_removal(client):
    ingredient, recipe, meals = seed(client)
    update(client, meals[0], dishes=[{'ingredient_id': ingredient, 'quantity': 30, 'unit': 'g'}])
    call(client, 'post', '/weeks/2026-11-09/template', expected=409)
    call(client, 'post', f"/meals/{meals[0]['id']}/suggestion", {'operation_id': str(uuid4()), 'recipe_id': recipe}, expected=409)
    update(client, meals[0], dishes=[], side_ingredient=None)
    assert not dashboard(client)['shopping']['items']
    call(client, 'post', '/weeks/2026-11-09/template')


def test_invalid_additions_roll_back_meal_and_reject_wrong_units(client):
    ingredient, recipe, meals = seed(client)
    plan(client, meals[0], recipe)
    before = dashboard(client)
    for extra in [
        {'side_id': recipe, 'side_ingredient': {'ingredient_id': ingredient, 'quantity': 1, 'unit': 'g'}},
        {'dishes': [{'ingredient_id': ingredient, 'quantity': 1, 'unit': 'l'}]},
        {'dishes': [{'title': 'Plat', 'recipe_id': recipe}]},
        {'dishes': [{'title': ''}]}, {'dishes': [{'title': 'Plat', 'course': 'invalide'}]}, {'dishes': [{'ingredient_id': ingredient}]},
        {'dishes': [{'title': 'Plat'}] * 21},
    ]:
        call(client, 'put', f"/meals/{meals[0]['id']}", {'status': 'maison', 'portions': 4, **extra}, expected=422)
        assert dashboard(client) == before


def test_fusion_updates_direct_ingredients_and_refuses_dimension_changes(client):
    ingredient, _, meals = seed(client)
    target = call(client, 'post', '/ingredients', {'name': 'Riz cible fictif', 'dimension': 'masse'})['id']
    update(client, meals[0], side_ingredient={'ingredient_id': ingredient, 'quantity': 50, 'unit': 'g'}, dishes=[{'ingredient_id': ingredient, 'quantity': 25, 'unit': 'g'}])
    call(client, 'put', f'/ingredients/{ingredient}', {'name': 'Riz volume fictif', 'dimension': 'volume'}, expected=409)
    preview = call(client, 'get', f'/ingredients/{ingredient}/merge-preview?target_id={target}')
    assert preview['counts']['meal_dishes'] == 2
    call(client, 'post', f'/ingredients/{ingredient}/merge', {'operation_id': str(uuid4()), 'target_id': target, 'preview_token': preview['token']})
    data = dashboard(client)
    assert data['week']['meals'][0]['side_ingredient']['ingredient_id'] == target
    assert data['shopping']['items'][0]['ingredient_id'] == target
    assert data['shopping']['items'][0]['quantity'] == 75


def test_backup_restores_all_additional_dishes(client, tmp_path):
    ingredient, _, meals = seed(client)
    update(client, meals[0], dishes=[{'title': 'Plat fictif'}, {'ingredient_id': ingredient, 'quantity': 60, 'unit': 'g'}])
    saved, restored = tmp_path / 'saved.sqlite3', tmp_path / 'restored.sqlite3'
    backup(tmp_path / 'mijote.sqlite3', saved)
    restore(saved, restored)
    with connect(restored) as db:
        assert db.execute('SELECT COUNT(*) FROM meal_dishes').fetchone()[0] == 2
        assert not db.execute('PRAGMA foreign_key_check').fetchall()


def test_courses_persist_in_planning_history_and_reuse(client):
    ingredient, recipe, meals = seed(client)
    update(client, meals[0], recipe_id=recipe, dishes=[
        {'title': 'Dessert fictif', 'course': 'dessert'},
        {'ingredient_id': ingredient, 'quantity': 30, 'unit': 'g', 'course': 'entree'},
    ])
    saved = dashboard(client)['week']['meals'][0]
    assert [d['course'] for d in saved['dishes']] == ['dessert', 'entree']
    assert dashboard(client)['shopping']['items'][0]['quantity'] == 130
    call(client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': str(uuid4())})
    event = call(client, 'get', '/history')['items'][0]
    assert [d['course'] for d in event['dishes']] == ['dessert', 'entree']
    call(client, 'post', f"/meals/{meals[2]['id']}/reuse", {'operation_id': str(uuid4()), 'source_meal_id': meals[0]['id']})
    copied = dashboard(client)['week']['meals'][2]
    assert [d['course'] for d in copied['dishes']] == ['dessert', 'entree']
