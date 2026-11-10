from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from conftest import call, seed, plan

WEEKS = ['2026-11-09', '2026-11-16']


def combined(client):
    return call(client, 'post', '/shopping/selection', {'weeks': WEEKS})


def setup(client):
    ident, recipe, meals = seed(client, quantity=100)
    plan(client, meals[0], recipe)
    later = call(client, 'post', '/weeks', {'start': WEEKS[1]})['meals'][0]
    plan(client, later, recipe)
    return ident


def checked(client):
    item = combined(client)['items'][0]
    call(client, 'patch', '/shopping/selection/check', {'weeks': WEEKS, 'ingredient_id': item['ingredient_id'], 'checked': True, 'version': item['version']})
    return combined(client)['items'][0]


def body(item, **edit):
    return {'operation_id': str(uuid4()), 'weeks': WEEKS, 'items': [{'ingredient_id': item['ingredient_id'], 'requested_ingredient_id': item['ingredient_id'], 'quantity': item['quantity'], 'unit': item['unit'], 'version': item['version'], **edit}]}


def dashboard(client):
    return call(client, 'get', '/dashboard?start=' + WEEKS[0])


def test_combination_counts_stock_once_and_preserves_source_lists(client):
    ident = setup(client)
    call(client, 'post', '/stock', {'ingredient_id': ident, 'quantity': 50, 'unit': 'g'})
    for week in WEEKS:
        call(client, 'post', f'/weeks/{week}/shopping/manual', {'ingredient_id': ident, 'quantity': 25, 'unit': 'g'})
    before = [call(client, 'get', f'/weeks/{week}/shopping') for week in WEEKS]
    item = combined(client)['items'][0]
    assert item['quantity'] == 200  # 200 required - 50 stock + 50 manual
    assert len(item['sources']) == 4
    assert dashboard(client)['stock'][0]['quantity'] == 50
    assert [call(client, 'get', f'/weeks/{week}/shopping') for week in WEEKS] == before
    assert combined(client) == combined(client)


def test_partial_basket_and_stale_checks_are_explicit(client):
    ident = setup(client)
    call(client, 'patch', f'/weeks/{WEEKS[0]}/shopping/check', {'ingredient_id': ident, 'checked': True})
    partial = combined(client)['items'][0]
    assert partial['partially_checked'] and not partial['checked']
    checked(client)
    call(client, 'patch', '/shopping/selection/check', {'weeks': WEEKS, 'ingredient_id': ident, 'checked': False, 'version': partial['version']}, expected=409)
    assert combined(client)['items'][0]['checked']
    assert dashboard(client)['stock'] == []


def test_purchase_adds_one_lot_and_replay_is_idempotent(client):
    ident = setup(client)
    for week in WEEKS:
        call(client, 'post', f'/weeks/{week}/shopping/manual', {'ingredient_id': ident, 'quantity': 25, 'unit': 'g'})
    item = checked(client)
    payload = body(item, location='Cellier')
    assert call(client, 'post', '/shopping/selection/complete', payload)['purchased'] == 1
    assert call(client, 'post', '/shopping/selection/complete', payload)['purchased'] == 1
    data = dashboard(client)
    assert len(data['stock']) == len(data['movements']) == 1
    assert data['stock'][0]['quantity'] == 250 and data['stock'][0]['location'] == 'Cellier'
    assert combined(client)['items'] == []
    assert len(data['week']['meals']) == 14
    payload['items'][0]['quantity'] += 1
    call(client, 'post', '/shopping/selection/complete', payload, expected=409)


def test_unfound_items_stay_on_the_list_without_stock(client):
    setup(client)
    payload = body(checked(client), found=False)
    assert call(client, 'post', '/shopping/selection/complete', payload)['purchased'] == 0
    assert dashboard(client)['stock'] == []
    item = combined(client)['items'][0]
    assert item['quantity'] == 200 and not item['checked']


def test_substitution_uses_the_real_ingredient_without_changing_meals(client):
    ident = setup(client)
    other = call(client, 'post', '/ingredients', {'name': 'Quinoa de test', 'dimension': 'masse'})['id']
    payload = body(checked(client), ingredient_id=other, quantity=0.25, unit='kg')
    call(client, 'post', '/shopping/selection/complete', payload)
    lot = dashboard(client)['stock'][0]
    assert lot['ingredient_id'] == other and lot['quantity'] == 250
    assert combined(client)['items'][0]['ingredient_id'] == ident
    assert combined(client)['items'][0]['quantity'] == 200  # no invented equivalence


def test_stale_purchase_and_invalid_unit_are_atomic(client):
    ident = setup(client)
    item = checked(client)
    before = dashboard(client)
    call(client, 'post', '/shopping/selection/complete', body(item, unit='l'), expected=422)
    assert dashboard(client)['stock'] == before['stock']
    call(client, 'post', '/stock', {'ingredient_id': ident, 'quantity': 50, 'unit': 'g'})
    before = dashboard(client)
    call(client, 'post', '/shopping/selection/complete', body(item), expected=409)
    assert dashboard(client)['stock'] == before['stock']
    assert dashboard(client)['movements'] == before['movements']


def test_concurrent_retries_do_not_duplicate_stock(client):
    setup(client)
    payload = body(checked(client))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post('/api/v1/shopping/selection/complete', json=payload), range(2)))
    assert [r.status_code for r in results] == [200, 200]
    assert len(dashboard(client)['stock']) == 1


def test_week_selection_rejects_duplicates_non_mondays_and_missing_weeks(client):
    setup(client)
    for weeks in [[WEEKS[0], WEEKS[0]], ['2026-11-10'], WEEKS * 7, []]:
        call(client, 'post', '/shopping/selection', {'weeks': weeks}, expected=422)
    call(client, 'post', '/shopping/selection', {'weeks': ['2027-01-04']}, expected=404)


def test_multiple_groups_are_all_validated_before_any_purchase(client):
    setup(client)
    other = call(client, 'post', '/ingredients', {'name': 'Boîte de test', 'dimension': 'piece'})['id']
    call(client, 'post', f'/weeks/{WEEKS[1]}/shopping/manual', {'ingredient_id': other, 'quantity': 1, 'unit': 'piece'})
    for item in combined(client)['items']:
        call(client, 'patch', '/shopping/selection/check', {'weeks': WEEKS, 'ingredient_id': item['ingredient_id'], 'checked': True, 'version': item['version']})
    items = combined(client)['items']
    payload = {'operation_id': str(uuid4()), 'weeks': WEEKS, 'items': [{'ingredient_id': i['ingredient_id'], 'requested_ingredient_id': i['ingredient_id'], 'quantity': i['quantity'], 'unit': i['unit'], 'version': i['version']} for i in items]}
    payload['items'][-1]['version'] = '0' * 64
    before = dashboard(client)
    call(client, 'post', '/shopping/selection/complete', payload, expected=409)
    after = dashboard(client)
    assert after['stock'] == before['stock'] and after['movements'] == before['movements']
    assert all(item['checked'] for item in combined(client)['items'])
