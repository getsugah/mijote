from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from conftest import call, seed, plan


def dashboard(client):
    return call(client, 'get', '/dashboard?start=2026-11-09')


def test_full_family_acceptance_and_idempotent_confirmations(client):
    settings = call(client, 'get', '/settings')
    next(p for p in settings['presence'] if p['day'] == 0 and p['slot'] == 'midi')['status'] = 'travail'
    call(client, 'put', '/settings', settings)
    ingredient, recipe, meals = seed(client, quantity=200)
    lunch = next(m for m in meals if m['slot'] == 'midi')
    assert lunch['status'] == 'travail'
    plan(client, lunch, recipe)
    assert next(p for p in call(client, 'get', '/settings')['presence'] if p['day'] == 0 and p['slot'] == 'midi')['status'] == 'travail'
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 50, 'unit': 'g', 'location': 'Placard'})
    assert dashboard(client)['shopping']['items'][0]['quantity'] == 150
    call(client, 'patch', '/weeks/2026-11-09/shopping/check', {'ingredient_id': ingredient, 'checked': True})
    assert sum(x['quantity'] for x in dashboard(client)['stock']) == 50  # checking is not buying
    purchase = {'operation_id': str(uuid4()), 'items': [{'ingredient_id': ingredient, 'quantity': 150, 'unit': 'g', 'location': 'Placard'}]}
    first = call(client, 'post', '/weeks/2026-11-09/shopping/complete', purchase)
    assert call(client, 'post', '/weeks/2026-11-09/shopping/complete', purchase) == first
    assert sum(x['quantity'] for x in dashboard(client)['stock']) == 200
    assert not dashboard(client)['shopping']['items']
    request = {'operation_id': str(uuid4())}
    prepared = call(client, 'post', f"/meals/{lunch['id']}/prepare", request)
    assert not prepared['shortages']
    assert call(client, 'post', f"/meals/{lunch['id']}/prepare", request) == prepared
    assert sum(x['quantity'] for x in dashboard(client)['stock']) == 0
    assert sum(x['delta'] for x in dashboard(client)['movements']) == 0


def test_reservations_share_stock_and_release_without_movements(client):
    ingredient, recipe, meals = seed(client)
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 150, 'unit': 'g'})
    plan(client, meals[0], recipe)
    plan(client, meals[1], recipe)
    d = dashboard(client)
    assert d['shopping']['needs']['items'][0]['reserved'] == 150
    assert d['shopping']['items'][0]['quantity'] == 50
    assert len(d['movements']) == 1
    plan(client, meals[0], recipe, status='travail')
    assert not dashboard(client)['shopping']['items']
    assert call(client, 'get', '/weeks/2026-11-09')['meals'][0]['recipe_id'] == recipe
    plan(client, meals[0], recipe)
    assert dashboard(client)['shopping']['items'][0]['quantity'] == 50


def test_reservations_also_cover_other_weeks(client):
    ingredient, recipe, meals = seed(client)
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 100, 'unit': 'g'})
    plan(client, meals[0], recipe)
    later = call(client, 'post', '/weeks', {'start': '2026-11-16'})['meals'][0]
    plan(client, later, recipe)
    assert call(client, 'get', '/weeks/2026-11-16/needs')['items'][0]['missing'] == 100
    assert dashboard(client)['shopping']['needs']['items'][0]['missing'] == 0


def test_portions_and_unit_conversion_and_side_dish(client):
    ingredient, recipe, meals = seed(client, quantity=1, unit='kg', portions=4)
    plan(client, meals[0], recipe, portions=2, side=recipe)
    item = dashboard(client)['shopping']['items'][0]
    assert item['quantity'] == 1000 and item['unit'] == 'g'
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 1, 'unit': 'l'}, expected=422)
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': -1, 'unit': 'g'}, expected=422)
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 0.0001, 'unit': 'g'}, expected=422)


def test_small_fraction_does_not_disappear(client):
    _, recipe, meals = seed(client, quantity=0.001, portions=3)
    plan(client, meals[0], recipe, portions=1)
    assert dashboard(client)['shopping']['items'][0]['quantity'] == 0.001


def test_preparation_shortage_does_not_block_or_go_negative(client):
    ingredient, recipe, meals = seed(client, quantity=200)
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 30, 'unit': 'g'})
    plan(client, meals[0], recipe)
    result = call(client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': str(uuid4())})
    assert result['shortages'][0]['quantity'] == 170
    assert all(x['quantity'] >= 0 for x in dashboard(client)['stock'])
    assert not dashboard(client)['shopping']['items']
    again = call(client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': str(uuid4())})
    assert again['already_prepared']
    assert len(dashboard(client)['movements']) == 2


def test_corrected_consumption_and_simple_meals(client):
    ingredient, recipe, meals = seed(client)
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 100, 'unit': 'g'})
    plan(client, meals[0], recipe)
    call(client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': str(uuid4()), 'quantities': [{'ingredient_id': ingredient, 'quantity': 40, 'unit': 'g'}]})
    assert sum(x['quantity'] for x in dashboard(client)['stock']) == 60
    simple = call(client, 'post', '/recipes', {'name': 'Restes du frigo', 'kind': 'simple'})['id']
    plan(client, meals[1], simple)
    call(client, 'post', f"/meals/{meals[1]['id']}/prepare", {'operation_id': str(uuid4())})
    assert sum(x['quantity'] for x in dashboard(client)['stock']) == 60
    assert not dashboard(client)['shopping']['items']


def test_frozen_prepared_meal_and_non_home_refused(client):
    _, recipe, meals = seed(client)
    plan(client, meals[0], recipe, status='exterieur')
    call(client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': str(uuid4())}, expected=409)
    plan(client, meals[0], recipe)
    call(client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': str(uuid4())})
    call(client, 'put', f"/meals/{meals[0]['id']}", {'status': 'travail', 'title': '', 'portions': 4}, expected=409)


def test_shopping_substitution_and_manual_list_scope(client):
    ingredient, _, _ = seed(client)
    replacement = call(client, 'post', '/ingredients', {'name': 'Quinoa', 'dimension': 'masse'})['id']
    manual = call(client, 'post', '/weeks/2026-11-09/shopping/manual', {'ingredient_id': ingredient, 'quantity': 500, 'unit': 'g'})['id']
    call(client, 'post', '/weeks', {'start': '2026-11-16'})
    assert not call(client, 'get', '/weeks/2026-11-16/shopping')['items']
    call(client, 'patch', '/weeks/2026-11-09/shopping/check', {'manual_id': manual, 'checked': True})
    request = {'operation_id': str(uuid4()), 'items': [{'manual_id': manual, 'ingredient_id': replacement, 'quantity': 400, 'unit': 'g'}]}
    call(client, 'post', '/weeks/2026-11-09/shopping/complete', request)
    assert dashboard(client)['stock'][0]['ingredient_id'] == replacement
    assert not dashboard(client)['shopping']['items']
    request['operation_id'] = str(uuid4())
    call(client, 'post', '/weeks/2026-11-09/shopping/complete', request, expected=409)


def test_purchase_is_atomic_and_requires_checked_items(client):
    ingredient, _, _ = seed(client)
    manual = call(client, 'post', '/weeks/2026-11-09/shopping/manual', {'ingredient_id': ingredient, 'quantity': 10, 'unit': 'g'})['id']
    request = {'operation_id': str(uuid4()), 'items': [{'manual_id': manual, 'ingredient_id': ingredient, 'quantity': 10, 'unit': 'g'}]}
    call(client, 'post', '/weeks/2026-11-09/shopping/complete', request, expected=409)
    call(client, 'patch', '/weeks/2026-11-09/shopping/check', {'manual_id': manual, 'checked': True})
    request['items'].append({'ingredient_id': ingredient, 'quantity': 1, 'unit': 'g'})
    call(client, 'post', '/weeks/2026-11-09/shopping/complete', request, expected=409)
    assert not dashboard(client)['stock']
    assert dashboard(client)['shopping']['items'][0]['checked']


def test_operation_reuse_with_different_payload_is_rejected(client):
    _, recipe, meals = seed(client)
    plan(client, meals[0], recipe)
    ident = str(uuid4())
    call(client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': ident})
    call(client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': ident, 'quantities': []}, expected=409)


def test_two_simultaneous_confirmations_deduct_once(client):
    ingredient, recipe, meals = seed(client)
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 200, 'unit': 'g'})
    plan(client, meals[0], recipe)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(call, client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': str(uuid4())}) for _ in range(2)]
        results = [f.result() for f in futures]
    assert sorted(r['already_prepared'] for r in results) == [False, True]
    assert sum(x['quantity'] for x in dashboard(client)['stock']) == 100


def test_stock_correction_is_logged_and_consumes_expiring_lot_first(client):
    ingredient, recipe, meals = seed(client)
    first = call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 100, 'unit': 'g', 'expires': '2027-01-01'})['id']
    soon = call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 100, 'unit': 'g', 'expires': '2026-11-10'})['id']
    plan(client, meals[0], recipe)
    call(client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': str(uuid4())})
    assert next(x for x in dashboard(client)['stock'] if x['id'] == soon)['quantity'] == 0
    call(client, 'patch', f'/stock/{first}', {'quantity': 25, 'unit': 'g', 'reason': 'Inventaire corrigé'})
    assert dashboard(client)['movements'][0]['delta'] == -75


def test_recipe_and_ingredient_crud_preserves_references(client):
    ingredient, recipe, meals = seed(client)
    call(client, 'put', f'/ingredients/{ingredient}', {'name': 'Riz long', 'dimension': 'masse'})
    call(client, 'put', f'/ingredients/{ingredient}', {'name': 'Riz long', 'dimension': 'volume'}, expected=409)
    call(client, 'put', f'/recipes/{recipe}', {'name': 'Riz du soir', 'kind': 'simple'})
    plan(client, meals[0], recipe)
    call(client, 'delete', f'/recipes/{recipe}', expected=409)
    plan(client, meals[0], None)
    call(client, 'delete', f'/recipes/{recipe}')
    call(client, 'delete', f'/ingredients/{ingredient}')
    assert not dashboard(client)['recipes'] and not dashboard(client)['ingredients']


def test_week_creation_is_idempotent_and_does_not_apply_new_template(client):
    _, _, meals = seed(client)
    settings = call(client, 'get', '/settings')
    settings['portions'] = 2
    settings['presence'][0]['status'] = 'travail'
    call(client, 'put', '/settings', settings)
    assert call(client, 'post', '/weeks', {'start': '2026-11-09'})['meals'] == meals
    assert call(client, 'post', '/weeks', {'start': '2026-11-16'})['meals'][0]['portions'] == 2
    call(client, 'post', '/weeks', {'start': '2026-11-10'}, expected=422)


def test_explicit_template_application_only_changes_an_empty_week(client):
    _, recipe, _ = seed(client)
    settings = call(client, 'get', '/settings')
    settings['portions'] = 2
    next(p for p in settings['presence'] if p['day'] == 0 and p['slot'] == 'midi')['status'] = 'travail'
    call(client, 'put', '/settings', settings)
    week = call(client, 'post', '/weeks/2026-11-09/template', {})
    assert week['meals'][0]['status'] == 'travail' and week['meals'][0]['portions'] == 2
    plan(client, week['meals'][0], recipe)
    call(client, 'post', '/weeks/2026-11-09/template', {}, expected=409)
    assert call(client, 'get', '/weeks/2026-11-09')['meals'][0]['recipe_id'] == recipe
