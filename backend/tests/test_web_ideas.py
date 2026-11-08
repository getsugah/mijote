import pytest

from app import web_ideas as web
from app.safe_fetch import ImportProblem
from conftest import call

# Synthetic links and names only, never a copy of the live site's contents.
URL_A = 'https://cuisine.journaldesfemmes.fr/recette/1000001-plat-temoin'
URL_B = 'https://cuisine.journaldesfemmes.fr/recette/1000002-autre-plat-temoin'
HTML = f'<a href="{URL_A}"><h2>Plat témoin</h2></a><a href="{URL_B}">Autre plat témoin</a>'


@pytest.fixture(autouse=True)
def empty_cache(monkeypatch):
    monkeypatch.setattr(web, '_cached', ())
    monkeypatch.setattr(web, '_expires', 0)


def test_parser_deduplicates_and_ignores_non_recipe_and_unsafe_links():
    hostile = '''<a href="javascript:alert(1)">Script</a>
    <a href="https://other.example/recette/1000003-faux">Autre site</a>
    <a href="https://cuisine.journaldesfemmes.fr.evil.example/recette/1000003-faux">Faux domaine</a>
    <a href="//localhost/recette/1000003-faux">Local</a>
    <a href="https://cuisine.journaldesfemmes.fr:8443/recette/1000003-faux">Port</a>
    <a href="/gastronomie/1000003-article">Article</a>
    <a href="/recette/1000004-vide"><img src="/image.jpg"></a>'''
    items = web.parse_index(HTML + hostile + f'<a href="{URL_A}?tracking=yes#part">Doublon</a>', web.INDEX_URL)
    assert len(items) == 2
    assert items[0] == {'name': 'Plat témoin', 'url': URL_A, 'source': web.SOURCE}
    assert web.recipe_link(URL_A + '/?tracking=yes#part') == URL_A
    with pytest.raises(ImportProblem):
        web.parse_index(HTML, 'https://other.example/')
    with pytest.raises(ImportProblem):
        web.parse_index('<html>Indisponible</html>', web.INDEX_URL)


def test_discovery_filters_seen_and_saved_recipes_without_repeating(monkeypatch):
    monkeypatch.setattr(web, 'fetch_html', lambda url: (HTML, web.INDEX_URL))
    first = web.discover([], [])['item']
    second = web.discover([first['url']], [])['item']
    assert first['url'] != second['url']
    assert web.discover([first['url']], [second['url'] + '?tracking=yes'])['item'] is None


def test_index_fetch_is_fixed_cached_and_never_fetches_recipes(monkeypatch):
    fetched = []
    def fetch(url):
        fetched.append(url)
        return HTML, url
    monkeypatch.setattr(web, 'fetch_html', fetch)
    web.discover(['https://untrusted.example/ignored'], [])
    web.discover([], [])
    assert fetched == [web.INDEX_URL]
    monkeypatch.setattr(web, '_expires', 0)
    web.discover([], [])
    assert fetched == [web.INDEX_URL, web.INDEX_URL]


def test_failed_fetch_and_busy_catalogue_are_retryable(monkeypatch):
    def blocked(url):
        raise ImportProblem('Source indisponible')
    monkeypatch.setattr(web, 'fetch_html', blocked)
    with pytest.raises(ImportProblem, match='indisponible'):
        web.discover([], [])
    assert not web._lock.locked()
    web._lock.acquire()
    try:
        with pytest.raises(ImportProblem, match='déjà en cours'):
            web.discover([], [])
    finally:
        web._lock.release()
    monkeypatch.setattr(web, 'fetch_html', lambda url: (HTML, web.INDEX_URL))
    assert web.discover([], [])['item']


def test_api_discovery_never_changes_recipes_planning_stock_or_courses(client, monkeypatch):
    monkeypatch.setattr(web, 'fetch_html', lambda url: (HTML, web.INDEX_URL))
    call(client, 'post', '/recipes', {'name': 'Recette déjà enregistrée', 'source_url': URL_A})
    call(client, 'post', '/weeks', {'start': '2026-11-09'})
    before = call(client, 'get', '/dashboard?start=2026-11-09')
    result = call(client, 'post', '/suggestions/web', {'exclude': []})
    assert result['item']['url'] == URL_B
    assert call(client, 'post', '/suggestions/web', {'exclude': [URL_B]})['item'] is None
    assert call(client, 'get', '/dashboard?start=2026-11-09') == before
    assert result['item'].keys() == {'name', 'url', 'source'}


def test_api_requires_auth_csrf_valid_origin_and_bounded_input(client, monkeypatch):
    def unexpected(url):
        pytest.fail('No network request is permitted before authorization and validation')
    monkeypatch.setattr(web, 'fetch_html', unexpected)
    response = client.post('/api/v1/suggestions/web', json={}, headers={'X-CSRF-Token': ''})
    assert response.status_code == 403
    response = client.post('/api/v1/suggestions/web', json={}, headers={'Origin': 'https://untrusted.example'})
    assert response.status_code == 403
    call(client, 'post', '/suggestions/web', {'exclude': [URL_A] * 101}, expected=422)
    call(client, 'post', '/suggestions/web', {'exclude': ['x' * 2001]}, expected=422)
    call(client, 'post', '/suggestions/web', {'url': 'https://untrusted.example'}, expected=422)
    client.cookies.clear()
    call(client, 'post', '/suggestions/web', {}, expected=401)


def test_api_source_failure_visible_without_breaking_local_suggestions(client, monkeypatch):
    def blocked(url):
        raise ImportProblem('Site indisponible')
    monkeypatch.setattr(web, 'fetch_html', blocked)
    response = call(client, 'post', '/suggestions/web', {}, expected=422)
    assert 'Découverte web indisponible' in response['detail']
    assert call(client, 'get', '/suggestions?day=2026-11-09')['items'] == []
