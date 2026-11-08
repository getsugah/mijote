#!/usr/bin/env python3
"""Exercise import on a fresh isolated household; never overwrite a real account."""
import http.cookiejar
import json
import secrets
import sys
import urllib.error
import urllib.request
from uuid import uuid4


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:18082'
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    csrf = ''
    def api(path, method='GET', body=None):
        headers = {'Accept': 'application/json'}
        if method != 'GET':
            headers.update({'Content-Type': 'application/json', 'X-CSRF-Token': csrf})
        request = urllib.request.Request(base + '/api/v1' + path, headers=headers, method=method,
                                        data=json.dumps(body or {}).encode() if method != 'GET' else None)
        with opener.open(request, timeout=25) as response:
            return json.load(response)
    assert not api('/auth/status')['initialized'], 'Refusing to write into an existing household.'
    csrf = api('/auth/setup', 'POST', {'name': 'Maison import de validation', 'password': secrets.token_urlsafe(24)})['csrf']
    api('/weeks', 'POST', {'start': '2026-11-09'})
    dashboard = lambda: api('/dashboard?start=2026-11-09')
    before = dashboard()
    for url in ['https://www.marmiton.org/recettes/recette_soupe-de-legumes_222646.aspx',
                'https://www.750g.com/pate-a-crepes-r6965.htm']:
        value = api('/recipes/import/preview', 'POST', {'url': url})
        assert value['name'] and value['ingredients'] and value['steps']
        print('Public URL preview:', url, value['method'], len(value['ingredients']), 'ingredient lines')
    after = dashboard()
    for field in ['recipes', 'ingredients', 'stock', 'movements']:
        assert before[field] == after[field], field
    pasted = api('/recipes/import/preview', 'POST', {'mode': 'text', 'url': 'https://example.test/source',
        'text': 'Plat synthétique de validation\nPour 4 personnes\nIngrédients :\n200 g de riz de validation\nsel au goût\nPréparation :\nCuire puis servir.'})
    assert pasted['portions'] == 4 and pasted['ingredients'][0]['quantity'] == 200
    body = {'operation_id': str(uuid4()), 'recipe': {'name': pasted['name'], 'portions': 4, 'minutes': 20,
            'steps': pasted['steps'], 'source_url': pasted['source_url'], 'source_author': 'Validation privée',
            'ingredient_notes': pasted['ingredient_notes']},
            'items': [{'name': 'riz de validation', 'quantity': 200, 'unit': 'g'}]}
    first = api('/recipes/import/confirm', 'POST', body)
    assert api('/recipes/import/confirm', 'POST', body) == first
    state = dashboard()
    assert len(state['recipes']) == 1 and len(state['ingredients']) == 1
    assert state['recipes'][0]['source_author'] == 'Validation privée'
    assert 'sel au goût' in state['recipes'][0]['ingredient_notes']
    assert not state['stock'] and not state['movements']
    try:
        api('/recipes/import/preview', 'POST', {'url': 'http://127.0.0.1/'})
        raise AssertionError('Private fetch must be refused')
    except urllib.error.HTTPError as error:
        assert error.code == 422
    print('Import HTTP acceptance: public previews are read-only; synthetic confirmation is atomic/idempotent; private URL refused.')


if __name__ == '__main__':
    main()
