import json
from io import BytesIO
import sqlite3

import pytest
from PIL import Image

from app import mealdb
from app.safe_fetch import ImportProblem
from conftest import call


def record(**overrides):
    return {'idMeal': '12345', 'strMeal': 'Chicken Curry', 'strMealThumb': 'https://www.themealdb.com/images/media/meals/example123.jpg',
            'strCategory': 'Chicken', 'strArea': 'India', 'strTags': 'Curry,MainMeal,Dinner',
            'strSource': 'https://recipes.example/curry', 'strImageSource': '', **overrides}


def mock_api(monkeypatch, payload):
    calls = []
    def fetch(url):
        calls.append(url)
        return json.dumps(payload), url
    monkeypatch.setattr(mealdb, 'fetch_html', fetch)
    return calls


def test_french_alias_search_returns_paired_titles_photos_and_explicit_metadata(monkeypatch):
    calls = mock_api(monkeypatch, {'meals': [record(), record(), record(idMeal='67890', strMeal='Another Curry')]})
    result = mealdb.search('  Poulet au curry  ')
    assert len(calls) == 1 and calls[0].endswith('search.php?s=chicken+curry')
    assert result['adapted'] and result['query_used'] == 'chicken curry'
    assert len(result['items']) == 2
    item = result['items'][0]
    assert item['title'] == 'Chicken Curry' and item['image_url'].endswith('example123.jpg')
    assert {'Cuisine indienne', 'Curry', 'Plat principal', 'Dîner'} <= set(item['tags'])
    assert item['provider'] == 'TheMealDB'
    assert item['attribution'] == 'TheMealDB · Chicken Curry'


def test_empty_and_bounded_results_do_not_invent_matches(monkeypatch):
    mock_api(monkeypatch, {'meals': None})
    result = mealdb.search('Plat inconnu')
    assert result['items'] == [] and 'Aucun résultat' in result['message']
    mock_api(monkeypatch, {'meals': [record(idMeal=str(i)) for i in range(1, 20)]})
    assert len(mealdb.search('curry')['items']) == 6


@pytest.mark.parametrize('payload', ['not json', '[]', '{}', '{"meals":"wrong"}', '{"meals":[null]}'])
def test_invalid_provider_responses_raise_visible_errors(monkeypatch, payload):
    monkeypatch.setattr(mealdb, 'fetch_html', lambda url: (payload, url))
    with pytest.raises(ImportProblem):
        mealdb.search('curry')


def test_untrusted_image_urls_are_never_displayed_or_downloaded(monkeypatch):
    for url in ['http://127.0.0.1/photo.jpg', 'https://photos.example/picture.jpg', 'https://www.themealdb.com/other/path.jpg', 'https://www.themealdb.com/images/media/meals/picture.jpg?redirect=1']:
        mock_api(monkeypatch, {'meals': [record(strMealThumb=url)]})
        assert mealdb.search('curry')['items'][0]['image_url'] == ''
        with pytest.raises(ImportProblem, match='Aucune photo'):
            mealdb.preview_photo('12345')


def test_photo_preview_downloads_official_image_and_retains_attribution(monkeypatch):
    calls = mock_api(monkeypatch, {'meals': [record()]})
    image = BytesIO(); Image.new('RGB', (20, 12), 'orange').save(image, 'JPEG')
    monkeypatch.setattr(mealdb, 'fetch_image', lambda url: (image.getvalue(), url))
    result = mealdb.preview_photo('12345')
    assert calls[0].endswith('lookup.php?i=12345')
    assert result['data_base64'] and result['width'] == 20
    assert result['source_url'].startswith('https://www.themealdb.com/images/media/meals/')
    assert 'TheMealDB' in result['attribution']


def test_preview_rejects_id_mismatch_and_final_source_change(monkeypatch):
    mock_api(monkeypatch, {'meals': [record(idMeal='22222')]})
    with pytest.raises(ImportProblem): mealdb.preview_photo('12345')
    mock_api(monkeypatch, {'meals': [record()]})
    monkeypatch.setattr(mealdb, 'fetch_image', lambda url: (b'not-used', 'https://photos.example/changed.jpg'))
    with pytest.raises(ImportProblem, match='changé de source'): mealdb.preview_photo('12345')


def test_search_and_preview_endpoints_are_read_only_authenticated_and_csrf_protected(client, tmp_path, monkeypatch):
    mock_api(monkeypatch, {'meals': [record()]})
    path = tmp_path / 'mijote.sqlite3'
    with sqlite3.connect(path) as db: before = '\n'.join(db.iterdump())
    result = call(client, 'post', '/recipes/search/mealdb', {'query': 'poulet au curry'})
    assert result['items'][0]['title'] == 'Chicken Curry'
    with sqlite3.connect(path) as db: assert '\n'.join(db.iterdump()) == before
    token = client.headers.pop('X-CSRF-Token')
    call(client, 'post', '/recipes/search/mealdb', {'query': 'curry'}, expected=403)
    client.headers['X-CSRF-Token'] = token
    call(client, 'post', '/recipes/search/mealdb/photo', {'meal_id': '../bad'}, expected=422)
    call(client, 'post', '/auth/logout')
    call(client, 'post', '/recipes/search/mealdb', {'query': 'curry'}, expected=401)


def test_invalid_key_and_cross_domain_api_response_are_rejected(monkeypatch):
    monkeypatch.setenv('MIJOTE_THEMEALDB_KEY', 'invalid/key')
    with pytest.raises(ImportProblem, match='configuration'): mealdb.search('curry')
    monkeypatch.setenv('MIJOTE_THEMEALDB_KEY', '1')
    monkeypatch.setattr(mealdb, 'fetch_html', lambda url: ('{"meals":null}', 'https://other.example/'))
    with pytest.raises(ImportProblem, match='inattendue'): mealdb.search('curry')
