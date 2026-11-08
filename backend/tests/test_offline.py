from uuid import uuid4
from conftest import call, seed, plan


def setup_list(client):
    ingredient, recipe, meals = seed(client)
    plan(client, meals[0], recipe)
    snapshot = call(client, 'get', '/weeks/2026-11-09/shopping/offline')
    return ingredient, snapshot


def op(item, action='check', **fields):
    return {'operation_id': str(uuid4()), 'week_start': '2026-11-09', 'action': action,
            'item_key': item['key'], 'expected_version': item['version'], **fields}


def sync(client, snapshot, operations):
    return call(client, 'post', '/shopping/sync', {'household_id': snapshot['household_id'], 'operations': operations})['results']


def test_checks_sync_once_without_modifying_stock(client):
    _, snapshot = setup_list(client)
    body = op(snapshot['items'][0], checked=True)
    first = sync(client, snapshot, [body])
    assert first[0]['status'] == 'applied' and sync(client, snapshot, [body]) == first
    data = call(client, 'get', '/dashboard?start=2026-11-09')
    assert data['shopping']['items'][0]['checked'] and not data['stock'] and not data['movements']


def test_other_device_change_causes_visible_conflict_even_after_aba(client):
    ingredient, snapshot = setup_list(client)
    for checked in (True, False):
        call(client, 'patch', '/weeks/2026-11-09/shopping/check', {'ingredient_id': ingredient, 'checked': checked})
    result = sync(client, snapshot, [op(snapshot['items'][0], checked=True)])
    assert result[0]['status'] == 'conflict'
    assert not call(client, 'get', '/weeks/2026-11-09/shopping')['items'][0]['checked']


def test_partial_sync_keeps_conflicts_and_applies_independent_manual_adds(client):
    ingredient, snapshot = setup_list(client)
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 100, 'unit': 'g'})
    add = {'operation_id': str(uuid4()), 'week_start': '2026-11-09', 'action': 'add', 'ingredient_id': ingredient, 'quantity': 25, 'unit': 'g', 'checked': True}
    results = sync(client, snapshot, [op(snapshot['items'][0], checked=True), add])
    assert [r['status'] for r in results] == ['conflict', 'applied']
    assert sync(client, snapshot, [add])[0]['status'] == 'applied'
    items = call(client, 'get', '/weeks/2026-11-09/shopping')['items']
    assert len(items) == 1 and items[0]['quantity'] == 25 and items[0]['checked']
    assert sum(s['quantity'] for s in call(client, 'get', '/dashboard?start=2026-11-09')['stock']) == 100


def test_manual_edit_remove_and_wrong_household_are_guarded(client):
    ingredient, snapshot = setup_list(client)
    add = {'operation_id': str(uuid4()), 'week_start': '2026-11-09', 'action': 'add', 'ingredient_id': ingredient, 'quantity': 10, 'unit': 'g'}
    sync(client, snapshot, [add])
    current = call(client, 'get', '/weeks/2026-11-09/shopping/offline')
    item = next(i for i in current['items'] if i['manual_id'])
    edit = op(item, 'edit', quantity=20, unit='g', checked=False)
    assert sync(client, snapshot, [edit])[0]['status'] == 'applied'
    assert sync(client, snapshot, [op(item, 'remove')])[0]['status'] == 'conflict'
    fresh = call(client, 'get', '/weeks/2026-11-09/shopping/offline')
    item = next(i for i in fresh['items'] if i['manual_id'])
    assert sync(client, fresh, [op(item, 'remove')])[0]['status'] == 'applied'
    call(client, 'post', '/shopping/sync', {'household_id': str(uuid4()), 'operations': [add]}, expected=409)
