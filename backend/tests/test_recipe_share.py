import json
import re
import sqlite3
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def receiver(tmp_path, monkeypatch):
    static = tmp_path / 'static'
    (static / 'assets').mkdir(parents=True)
    (static / 'index.html').write_text('<html><head><title>Mijote</title></head><body><div id="app"></div><script type="module" src="/assets/app.js"></script></body></html>')
    monkeypatch.setenv('MIJOTE_STATIC_DIR', str(static))
    database = tmp_path / 'mijote.sqlite3'
    with TestClient(create_app(database, secure_cookie=False)) as client:
        yield client, database


def test_share_is_received_before_login_without_database_writes_or_fetch(receiver, monkeypatch):
    from app import recipe_import
    monkeypatch.setattr(recipe_import, 'preview', lambda *args: pytest.fail('A share must not fetch a recipe automatically'))
    client, database = receiver
    response = client.post('/share-recipe', data={'title': 'Soupe témoin', 'text': 'Une idée pour ce soir', 'url': 'https://recettes.example/soupe'})
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['referrer-policy'] == 'no-referrer'
    assert 'script-src \'self\'' in response.headers['content-security-policy']
    assert 'set-cookie' not in response.headers
    marker = re.search(r'<script type="application/json" id="mijote-recipe-share">(.*?)</script>', response.text).group(1)
    assert json.loads(marker)['url'] == 'https://recettes.example/soupe'
    with sqlite3.connect(database) as db:
        for table in ('users','recipes','ingredients','stock','movements','operations'):
            assert db.execute(f'SELECT count(*) FROM {table}').fetchone()[0] == 0
    assert not client.get('/api/v1/auth/status').json()['initialized']


def test_shared_html_is_inert_and_cannot_close_the_json_element(receiver):
    client, _ = receiver
    payload = '</script><img src=x onerror=alert(1)><script>alert(1)</script>'
    response = client.post('/share-recipe', data={'text': payload})
    assert response.status_code == 200
    assert payload not in response.text and '<img src=x' not in response.text
    marker = re.search(r'id="mijote-recipe-share">(.*?)</script>', response.text).group(1)
    assert json.loads(marker)['text'] == payload


@pytest.mark.parametrize('body', [
    {}, {'title': 'a'*301}, {'url': 'a'*2001}, {'text': 'a'*60001},
    {'title':'a','text':'b','url':'c','files':'d'}, {'title':['a','b']},
])
def test_invalid_or_oversized_fields_are_rejected(receiver, body):
    client, _ = receiver
    response = client.post('/share-recipe', content=urlencode(body, doseq=True), headers={'content-type':'application/x-www-form-urlencoded'})
    assert response.status_code == 422
    assert response.headers['cache-control'] == 'no-store'


def test_streamed_body_is_bounded_even_without_content_length(receiver):
    client, _ = receiver
    response = client.post('/share-recipe', content=(b'a'*100000 for _ in range(3)), headers={'content-type':'application/x-www-form-urlencoded'})
    assert response.status_code == 413


def test_json_files_and_invalid_encoding_are_rejected(receiver):
    client, _ = receiver
    assert client.post('/share-recipe', json={'url':'https://recettes.example'}).status_code == 415
    assert client.post('/share-recipe', files={'files':('test.txt',b'test')}).status_code == 415
    assert client.post('/share-recipe', content=b'text=%ff', headers={'content-type':'application/x-www-form-urlencoded'}).status_code == 422
