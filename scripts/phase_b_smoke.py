"""HTTP acceptance on a fresh, isolated loopback instance. Never initializes an existing home."""
import http.cookiejar
import json
import secrets
import sys
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4


def main():
    base = sys.argv[1].rstrip('/')
    parsed = urlsplit(base)
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or not parsed.port or parsed.port == 8080 or parsed.path:
        raise SystemExit('Utiliser une instance isolée sur loopback et un port de validation distinct.')
    opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
    csrf = ''

    def call(path, method='GET', body=None, expected=200):
        request = Request(base + '/api/v1' + path, method=method,
                          headers={'Content-Type': 'application/json', 'X-CSRF-Token': csrf},
                          data=json.dumps(body or {}).encode() if method != 'GET' else None)
        try:
            with opener.open(request, timeout=10) as response:
                status, content = response.status, response.read()
        except HTTPError as error:
            status, content = error.code, error.read()
        assert status == expected, (path, status, content.decode())
        return json.loads(content)

    assert not call('/auth/status')['initialized'], 'Instance déjà initialisée : aucune donnée modifiée.'
    call('/history', expected=401)
    session = call('/auth/setup', 'POST', {'name': 'Maison de validation', 'password': secrets.token_urlsafe(32)})
    csrf = session['csrf']
    household = session['household_id']
    ingredient = call('/ingredients', 'POST', {'name': 'Riz témoin', 'dimension': 'masse'})['id']
    recipe = call('/recipes', 'POST', {'name': 'Plat de validation', 'kind': 'recette', 'portions': 4, 'minutes': 15,
        'ingredients': [{'ingredient_id': ingredient, 'quantity': 100, 'unit': 'g'}]})['id']
    call(f'/recipes/{recipe}/preferences', 'PATCH', {'favorite': True, 'to_try': True, 'rating': 'a_refaire', 'category': 'vegetarien', 'comment': 'Essai synthétique', 'variant': 'Avec des herbes'})
    source = call('/weeks', 'POST', {'start': '2026-11-09'})['meals']
    planned = {'operation_id': str(uuid4()), 'recipe_id': recipe}
    assert call(f"/meals/{source[0]['id']}/suggestion", 'POST', planned) == call(f"/meals/{source[0]['id']}/suggestion", 'POST', planned)
    call('/stock', 'POST', {'ingredient_id': ingredient, 'quantity': 50, 'unit': 'g'})
    assert call('/weeks/2026-11-09/shopping')['items'][0]['quantity'] == 50
    assert not call('/history')['items']
    call(f"/meals/{source[0]['id']}/prepare", 'POST', {'operation_id': str(uuid4())})
    assert len(call('/history')['items']) == 1
    target = call('/weeks', 'POST', {'start': '2026-11-16'})['meals']
    preview = call('/weeks/2026-11-16/copy-preview?source_start=2026-11-09')
    assert len(preview['items']) == 1
    result = call('/weeks/2026-11-16/copy', 'POST', {'operation_id': str(uuid4()), 'source_start': '2026-11-09', 'preview_token': preview['preview_token']})
    assert result['copied'] == 1 and not call('/weeks/2026-11-16')['meals'][0]['prepared']
    call(f"/meals/{target[0]['id']}/suggestion", 'POST', {'operation_id': str(uuid4()), 'recipe_id': recipe}, expected=409)
    for mode in ('varier', 'stock', 'rapide', 'decouverte'):
        assert call('/suggestions?day=2026-11-16&mode=' + mode)['items'][0]['recipe_id'] == recipe
    snapshot = call('/weeks/2026-11-16/shopping/offline')
    before = call('/dashboard?start=2026-11-16')
    item = snapshot['items'][0]
    operation = {'operation_id': str(uuid4()), 'week_start': '2026-11-16', 'action': 'check', 'item_key': item['key'], 'expected_version': item['version'], 'checked': True}
    body = {'household_id': household, 'operations': [operation]}
    first = call('/shopping/sync', 'POST', body)
    assert first['results'][0]['status'] == 'applied' and call('/shopping/sync', 'POST', body) == first
    stale = {**operation, 'operation_id': str(uuid4()), 'checked': False}
    assert call('/shopping/sync', 'POST', {'household_id': household, 'operations': [stale]})['results'][0]['status'] == 'conflict'
    after = call('/dashboard?start=2026-11-16')
    assert before['stock'] == after['stock'] and before['movements'] == after['movements']
    assert len(call('/history')['items']) == 1
    assert after['recipes'][0]['favorite'] and not after['recipes'][0]['to_try']
    print('Phase B HTTP : préférences, historique réel, suggestions, copie protégée et synchronisation idempotente validés ; stock inchangé par la synchronisation.')


if __name__ == '__main__':
    main()
