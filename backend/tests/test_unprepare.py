from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from app.db import connect
from conftest import call, seed, plan


def dashboard(client):
    return call(client, 'get', '/dashboard?start=2026-11-09')


def prepare(client, meal, quantities=None):
    operation = str(uuid4())
    body = {'operation_id': operation}
    if quantities is not None:
        body['quantities'] = quantities
    call(client, 'post', f"/meals/{meal['id']}/prepare", body)
    return operation


def undo(client, meal, preparation, operation=None):
    return call(client, 'post', f"/meals/{meal['id']}/unprepare", {
        'operation_id': operation or str(uuid4()), 'preparation_id': preparation})


def test_undo_restores_only_actual_consumption_to_original_lots_and_recalculates(client):
    ingredient, recipe, meals = seed(client, quantity=200)
    plan(client, meals[0], recipe)
    plan(client, meals[2], recipe)
    for amount, location, expires in [(50, 'Placard', '2026-11-10'), (80, 'Congélateur', None)]:
        call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': amount, 'unit': 'g', 'location': location, 'expires': expires})
    lots = dashboard(client)['stock']
    active = prepare(client, meals[0])
    data = dashboard(client)
    assert data['week']['meals'][0]['preparation_id'] == active
    assert sum(x['quantity'] for x in data['stock']) == 0
    # Reconfirmation is a no-op and must not become the cancellation target.
    call(client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': str(uuid4())})
    assert dashboard(client)['week']['meals'][0]['preparation_id'] == active
    result = undo(client, meals[0], active)
    assert sum(x['quantity'] for x in result['restored']) == 130  # never restore the 70 g shortage
    data = dashboard(client)
    assert data['stock'] == lots
    assert data['week']['meals'][0]['prepared'] == 0
    assert data['week']['meals'][0]['preparation_id'] is None
    assert data['shopping']['needs']['items'][0]['required'] == 400
    assert data['shopping']['items'][0]['quantity'] == 270
    assert not call(client, 'get', '/history')['items']
    assert len(data['movements']) == 6  # both deductions and cancellations remain audited


def test_undo_uses_recorded_consumption_even_after_recipe_change(client):
    ingredient, recipe, meals = seed(client, quantity=200)
    plan(client, meals[0], recipe)
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 100, 'unit': 'g'})
    active = prepare(client, meals[0], [{'ingredient_id': ingredient, 'quantity': 40, 'unit': 'g'}])
    call(client, 'put', f'/recipes/{recipe}', {'name': 'Recette modifiée', 'portions': 4,
        'ingredients': [{'ingredient_id': ingredient, 'quantity': 900, 'unit': 'g'}]})
    result = undo(client, meals[0], active)
    assert result['restored'][0]['quantity'] == 40
    assert sum(x['quantity'] for x in dashboard(client)['stock']) == 100
    assert dashboard(client)['shopping']['items'][0]['quantity'] == 800


def test_replay_and_concurrent_cancellations_never_double_restore(client):
    ingredient, recipe, meals = seed(client)
    plan(client, meals[0], recipe)
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 100, 'unit': 'g'})
    active = prepare(client, meals[0])
    ident = str(uuid4())
    first = undo(client, meals[0], active, ident)
    assert undo(client, meals[0], active, ident) == first
    assert undo(client, meals[0], active)['already_unprepared']
    assert sum(x['quantity'] for x in dashboard(client)['stock']) == 100
    active = prepare(client, meals[0])
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(undo, client, meals[0], active) for _ in range(2)]
        results = [f.result() for f in futures]
    assert sorted(r['already_unprepared'] for r in results) == [False, True]
    assert sum(x['quantity'] for x in dashboard(client)['stock']) == 100


def test_reprepare_and_stale_cancellation_preserve_new_preparation(client):
    ingredient, recipe, meals = seed(client)
    plan(client, meals[0], recipe)
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 100, 'unit': 'g'})
    original = prepare(client, meals[0])
    cancellation = str(uuid4())
    undo(client, meals[0], original, cancellation)
    # A corrected meal can be edited and then prepared afresh.
    plan(client, meals[0], recipe, portions=2)
    current = prepare(client, meals[0])
    assert current != original
    body = {'operation_id': str(uuid4()), 'preparation_id': original}
    call(client, 'post', f"/meals/{meals[0]['id']}/unprepare", body, expected=409)
    undo(client, meals[0], original, cancellation)  # old UUID replays only its response
    assert dashboard(client)['week']['meals'][0]['preparation_id'] == current
    assert sum(x['quantity'] for x in dashboard(client)['stock']) == 50
    assert len(call(client, 'get', '/history')['items']) == 1
    undo(client, meals[0], current)
    assert sum(x['quantity'] for x in dashboard(client)['stock']) == 100


def test_no_stock_or_unquantified_meal_never_creates_fictitious_stock(client):
    _, recipe, meals = seed(client)
    plan(client, meals[0], recipe)
    active = prepare(client, meals[0])
    assert undo(client, meals[0], active)['restored'] == []
    assert not dashboard(client)['stock']
    simple = call(client, 'post', '/recipes', {'name': 'Plat fictif sans quantités', 'kind': 'simple'})['id']
    plan(client, meals[2], simple)
    active = prepare(client, meals[2])
    assert undo(client, meals[2], active)['restored'] == []
    assert not dashboard(client)['stock']


def test_undo_requires_session_csrf_and_matching_preparation(client):
    _, recipe, meals = seed(client)
    plan(client, meals[0], recipe)
    active = prepare(client, meals[0])
    url = f"/meals/{meals[0]['id']}/unprepare"
    body = {'operation_id': str(uuid4()), 'preparation_id': active}
    assert client.post('/api/v1' + url, json=body, headers={'X-CSRF-Token': ''}).status_code == 403
    call(client, 'post', url, {'operation_id': str(uuid4())}, expected=409)
    client.cookies.clear()
    call(client, 'post', url, body, expected=401)


def test_missing_audit_refuses_automatic_undo_without_changing_data(client, tmp_path):
    _, recipe, meals = seed(client)
    plan(client, meals[0], recipe)
    with connect(tmp_path / 'mijote.sqlite3') as db:
        db.execute('UPDATE meals SET prepared=1 WHERE id=?', (meals[0]['id'],))
    call(client, 'post', f"/meals/{meals[0]['id']}/unprepare", {'operation_id': str(uuid4())}, expected=409)
    assert dashboard(client)['week']['meals'][0]['prepared'] == 1
    assert not dashboard(client)['stock']
