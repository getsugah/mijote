#!/usr/bin/env python3
"""HTTP checks; --scenario initializes only a fresh, explicitly designated test household."""
import argparse
import http.cookiejar
import json
import secrets
import urllib.error
import urllib.request
from datetime import date, timedelta
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', nargs='?', default='http://127.0.0.1:8080')
    parser.add_argument('--scenario', action='store_true', help='Create test data only if the household is uninitialized')
    args = parser.parse_args()
    base = args.url.rstrip('/')
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    csrf = ''

    def request(path, method='GET', body=None):
        headers = {'Accept': 'application/json'}
        if method != 'GET':
            headers.update({'Content-Type': 'application/json', 'X-CSRF-Token': csrf})
        req = urllib.request.Request(base + path, method=method, headers=headers,
                                     data=json.dumps(body if body is not None else {}).encode() if method != 'GET' else None)
        with opener.open(req, timeout=15) as response:
            return response.read(), response.headers

    def api(path, method='GET', body=None):
        return json.loads(request('/api/v1' + path, method, body)[0])

    assert api('/health') == {'status': 'ok'}
    html = request('/')[0].decode()
    assert 'lang="fr"' in html and '/assets/' in html
    assert json.loads(request('/manifest.webmanifest')[0])['name'] == 'Mijote'
    for size in (192, 512):
        assert request(f'/icon-{size}.png')[0].startswith(b'\x89PNG')
    try:
        api('/settings')
        raise AssertionError('Unauthenticated data must not be accessible')
    except urllib.error.HTTPError as error:
        assert error.code == 401
    if not args.scenario:
        print('HTTP health, frontend, manifest, icons and unauthenticated access: passed.')
        return
    assert not api('/auth/status')['initialized'], 'Refusing to write into an existing household.'
    csrf = api('/auth/setup', 'POST', {'name': 'Maison de validation', 'password': secrets.token_urlsafe(24)})['csrf']
    settings = api('/settings')
    for entry in settings['presence']:
        if entry['day'] == 0 and entry['slot'] == 'midi':
            entry['status'] = 'travail'
    api('/settings', 'PUT', settings)
    monday = (date.today() - timedelta(days=date.today().weekday())).isoformat()
    week = api('/weeks', 'POST', {'start': monday})
    assert api(f'/weeks/{monday}/template', 'POST')['meals'] == week['meals']
    meal = week['meals'][0]
    assert meal['status'] == 'travail'
    ingredient = api('/ingredients', 'POST', {'name': 'Riz de validation', 'dimension': 'masse'})['id']
    recipe = api('/recipes', 'POST', {'name': 'Repas de validation', 'portions': 4,
        'ingredients': [{'ingredient_id': ingredient, 'quantity': 200, 'unit': 'g'}]})['id']
    api('/stock', 'POST', {'ingredient_id': ingredient, 'quantity': 50, 'unit': 'g'})
    api(f"/meals/{meal['id']}", 'PUT', {'status': 'maison', 'recipe_id': recipe, 'title': '', 'portions': 4})
    try:
        api(f'/weeks/{monday}/template', 'POST')
        raise AssertionError('A template must not overwrite a planned meal')
    except urllib.error.HTTPError as error:
        assert error.code == 409
    dashboard = lambda: api('/dashboard?start=' + monday)
    assert dashboard()['shopping']['items'][0]['quantity'] == 150
    api(f'/weeks/{monday}/shopping/check', 'PATCH', {'ingredient_id': ingredient, 'checked': True})
    assert sum(s['quantity'] for s in dashboard()['stock']) == 50
    purchase = {'operation_id': str(uuid4()), 'items': [{'ingredient_id': ingredient, 'quantity': 150, 'unit': 'g'}]}
    first = api(f'/weeks/{monday}/shopping/complete', 'POST', purchase)
    assert api(f'/weeks/{monday}/shopping/complete', 'POST', purchase) == first
    assert sum(s['quantity'] for s in dashboard()['stock']) == 200
    prepare = {'operation_id': str(uuid4())}
    first = api(f"/meals/{meal['id']}/prepare", 'POST', prepare)
    assert api(f"/meals/{meal['id']}/prepare", 'POST', prepare) == first
    result = dashboard()
    assert sum(s['quantity'] for s in result['stock']) == 0
    assert len(result['movements']) == 4  # two incoming lots, then one consumption per lot
    assert sum(entry['delta'] for entry in result['movements']) == 0
    assert not result['shopping']['items']
    # The household is still the disposable one created above, never a real installation.
    location = api('/locations', 'POST', {'name': 'Étagère de validation'})['name']
    assert location in api('/locations')
    lot = result['stock'][0]
    api(f"/stock/{lot['id']}", 'PATCH', {'version': lot['version'], 'name': 'Bocal de validation',
        'quantity': 40, 'unit': 'g', 'location': location, 'expires': None, 'reason': 'Inventaire fictif'})
    edited = next(item for item in dashboard()['stock'] if item['id'] == lot['id'])
    assert edited['name'] == 'Bocal de validation' and edited['location'] == location
    assert edited['ingredient_name'] == 'Riz de validation' and edited['quantity'] == 40
    second_week = (date.fromisoformat(monday) + timedelta(days=7)).isoformat()
    later = api('/weeks', 'POST', {'start': second_week})
    for target in [week['meals'][1], later['meals'][0]]:
        api(f"/meals/{target['id']}", 'PUT', {'status': 'maison', 'recipe_id': recipe, 'title': '', 'portions': 4})
    for key in [monday, second_week]:
        api(f'/weeks/{key}/shopping/manual', 'POST', {'ingredient_id': ingredient, 'quantity': 10, 'unit': 'g'})
    scope = {'weeks': [monday, second_week]}
    grouped = api('/shopping/selection', 'POST', scope)['items'][0]
    assert grouped['quantity'] == 380 and len(grouped['sources']) == 4
    api('/shopping/selection/check', 'PATCH', {**scope, 'ingredient_id': ingredient, 'checked': True, 'version': grouped['version']})
    assert sum(item['quantity'] for item in dashboard()['stock']) == 40
    grouped = api('/shopping/selection', 'POST', scope)['items'][0]
    purchase = {**scope, 'operation_id': str(uuid4()), 'items': [{'ingredient_id': ingredient,
        'requested_ingredient_id': ingredient, 'quantity': 380, 'unit': 'g', 'location': location,
        'version': grouped['version']}]}
    first = api('/shopping/selection/complete', 'POST', purchase)
    assert api('/shopping/selection/complete', 'POST', purchase) == first
    assert sum(item['quantity'] for item in dashboard()['stock']) == 420
    assert api('/shopping/selection', 'POST', scope)['items'] == []
    print('Container HTTP acceptance: stock editing, locations, combined weeks, purchases and preparation replay passed.')


if __name__ == '__main__':
    main()
