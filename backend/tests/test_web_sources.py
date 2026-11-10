import json
import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from app import web_ideas as web, safe_fetch
from app.backup import backup, restore
from app.db import migrate, connect
from app.safe_fetch import ImportProblem
from conftest import call

SOURCE = 'https://recettes.example/idees'
HTML = '''<a href="/recette/1000001-plat-fictif">Plat fictif</a>
<a href="/recette/1000002-autre-plat">Autre plat</a>'''


@pytest.fixture(autouse=True)
def no_cached_sources(monkeypatch):
    monkeypatch.setattr(web, '_custom_cache', web.OrderedDict())


def test_generic_index_and_structured_direct_recipe():
    items = web.parse_source(HTML, SOURCE)
    assert len(items) == 2 and items[0]['source'] == 'recettes.example'
    direct = '<script type="application/ld+json">' + json.dumps({'@type': 'Recipe', 'name': 'Plat fictif'}) + '</script>'
    assert web.parse_source(direct, SOURCE)[0]['url'] == SOURCE
    structured = '<script type="application/ld+json">' + json.dumps({'@type': 'ItemList', 'itemListElement': [
        {'@type': 'ListItem', 'item': {'name': 'Autre idée', 'url': '/plat-fictif'}},
        {'name': 'Sans lien'}, {'item': {'name': 'Faux', 'url': 'javascript:alert(1)'}},
        {'name': 'Mauvais domaine', 'item': 'https://other.example/plat'},
        {'item': {'name': 'Lien invalide', 'url': 'https://[invalide/'}}]}) + '</script>'
    assert [x['name'] for x in web.parse_source(structured, SOURCE)] == ['Autre idée']
    with pytest.raises(ImportProblem):
        web.parse_source('<a href="/contact">Contact</a><a href="https://[oops/">Lien</a>', SOURCE)


def test_add_list_select_remove_preserves_recipes_and_dashboard(client, monkeypatch):
    fetched = []
    def fetch(url):
        fetched.append(url)
        return HTML, url
    monkeypatch.setattr(web, 'fetch_html', fetch)
    call(client, 'post', '/weeks', {'start': '2026-11-09'})
    call(client, 'post', '/recipes', {'name': 'Mon plat existant'})
    before = call(client, 'get', '/dashboard?start=2026-11-09')
    added = call(client, 'post', '/suggestions/web/sources', {'url': SOURCE + '?utm_source=test#haut'})
    assert added['url'] == SOURCE and added['count'] == 2
    sources = call(client, 'get', '/suggestions/web/sources')['items']
    assert sources[0]['id'] == 0 and sources[1]['id'] == added['id']
    first = call(client, 'post', '/suggestions/web', {'source_id': added['id']})['item']
    second = call(client, 'post', '/suggestions/web', {'source_id': added['id'], 'exclude': [first['url']]})['item']
    assert first['url'] != second['url']
    assert fetched == [SOURCE]  # verification and suggestions share the bounded cache
    call(client, 'delete', f"/suggestions/web/sources/{added['id']}")
    assert len(call(client, 'get', '/suggestions/web/sources')['items']) == 1
    call(client, 'post', '/suggestions/web', {'source_id': added['id']}, expected=404)
    assert call(client, 'get', '/dashboard?start=2026-11-09') == before
    call(client, 'delete', '/suggestions/web/sources/0', expected=404)


def test_invalid_unreadable_duplicate_and_limit_do_not_save_extra_sources(client, monkeypatch):
    monkeypatch.setattr(web, 'fetch_html', lambda url: ('<h1>Aucune recette</h1>', url))
    call(client, 'post', '/suggestions/web/sources', {'url': SOURCE}, expected=422)
    call(client, 'post', '/suggestions/web/sources', {'url': 'javascript:alert(1)'}, expected=422)
    assert len(call(client, 'get', '/suggestions/web/sources')['items']) == 1
    monkeypatch.setattr(web, 'fetch_html', lambda url: (HTML, url))
    monkeypatch.setattr(web, 'MAX_SOURCES', 2)
    call(client, 'post', '/suggestions/web/sources', {'url': SOURCE})
    call(client, 'post', '/suggestions/web/sources', {'url': SOURCE + '#fragment'}, expected=409)
    call(client, 'post', '/suggestions/web/sources', {'url': SOURCE + '-2'})
    call(client, 'post', '/suggestions/web/sources', {'url': SOURCE + '-3'}, expected=409)
    assert len(web._custom_cache) <= 2


def test_private_source_never_opens_connection_or_saves(client, monkeypatch):
    def forbidden(*args):
        pytest.fail('A private destination must never open an HTTP connection')
    monkeypatch.setattr(safe_fetch, 'request_once', forbidden)
    call(client, 'post', '/suggestions/web/sources', {'url': 'http://127.0.0.1/'}, expected=422)
    assert len(call(client, 'get', '/suggestions/web/sources')['items']) == 1


def test_custom_source_saved_recipes_excluded_and_other_sources_isolated(client, monkeypatch):
    monkeypatch.setattr(web, 'fetch_html', lambda url: (HTML, url))
    first = call(client, 'post', '/suggestions/web/sources', {'url': SOURCE})
    second = call(client, 'post', '/suggestions/web/sources', {'url': 'https://other.example/idees'})
    call(client, 'post', '/recipes', {'name': 'Plat déjà dans le carnet', 'source_url': 'https://recettes.example/recette/1000001-plat-fictif?utm_campaign=test'})
    result = call(client, 'post', '/suggestions/web', {'source_id': first['id']})
    assert result['item']['name'] == 'Autre plat'
    result = call(client, 'post', '/suggestions/web', {'source_id': second['id']})
    assert result['item']['source'] == 'other.example'


def test_sources_require_session_csrf_and_valid_input(client, monkeypatch):
    monkeypatch.setattr(web, 'fetch_html', lambda url: pytest.fail('Unexpected fetch'))
    assert client.post('/api/v1/suggestions/web/sources', json={'url': SOURCE}, headers={'X-CSRF-Token': ''}).status_code == 403
    assert client.request('DELETE', '/api/v1/suggestions/web/sources/1', json={}, headers={'X-CSRF-Token': ''}).status_code == 403
    call(client, 'post', '/suggestions/web/sources', {'url': 'x' * 2001}, expected=422)
    call(client, 'post', '/suggestions/web', {'source_id': -1}, expected=422)
    client.cookies.clear()
    call(client, 'get', '/suggestions/web/sources', expected=401)
    call(client, 'post', '/suggestions/web/sources', {'url': SOURCE}, expected=401)


def test_links_survive_backup_and_restore(client, tmp_path, monkeypatch):
    monkeypatch.setattr(web, 'fetch_html', lambda url: (HTML, url))
    added = call(client, 'post', '/suggestions/web/sources', {'url': SOURCE})
    saved, restored = tmp_path / 'saved.sqlite3', tmp_path / 'restored.sqlite3'
    backup(tmp_path / 'mijote.sqlite3', saved)
    call(client, 'delete', f"/suggestions/web/sources/{added['id']}")
    restore(saved, restored)
    with sqlite3.connect(restored) as db:
        assert db.execute('SELECT url FROM web_sources').fetchall() == [(SOURCE,)]
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'


def test_migration_preserves_existing_recipes(tmp_path):
    path = tmp_path / 'old.sqlite3'
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / 'alembic.ini'))
    config.set_main_option('script_location', str(root / 'migrations'))
    config.set_main_option('sqlalchemy.url', 'sqlite:///' + str(path))
    command.upgrade(config, '0004')
    with connect(path) as db:
        db.execute("INSERT INTO recipes (name,kind,portions) VALUES ('Recette fictive','simple',4)")
    migrate(path)
    with connect(path) as db:
        assert db.execute('SELECT name FROM recipes').fetchone()[0] == 'Recette fictive'
        assert db.execute('SELECT COUNT(*) FROM web_sources').fetchone()[0] == 0
        assert db.execute('SELECT version_num FROM alembic_version').fetchone()[0] == '0008'
