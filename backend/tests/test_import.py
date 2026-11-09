import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

from app import recipe_import as parser
from app.db import migrate
from app.safe_fetch import ImportProblem
from conftest import call


def structured(**overrides):
    value = {'@type': 'Recipe', 'name': 'Soupe de test', 'recipeYield': '4 personnes',
             'recipeIngredient': ['200 g de légumes', '1 l d’eau', 'sel au goût'],
             'recipeInstructions': [{'@type': 'HowToSection', 'name': 'Préparer', 'itemListElement': [
                 {'@type': 'HowToStep', 'text': 'Couper les légumes.'}, {'@type': 'HowToStep', 'text': 'Faire cuire.'}]}],
             'totalTime': 'PT35M', 'author': {'@type': 'Person', 'name': 'Atelier de test'}}
    value.update(overrides)
    return '<html><script type="application/ld+json">' + json.dumps({'@graph': [value]}, ensure_ascii=False) + '</script></html>'


def test_jsonld_graph_sections_author_and_uncertain_ingredients():
    value = parser.parse_html(structured(), 'https://public.example/recette')
    assert value['method'] == 'jsonld' and value['name'] == 'Soupe de test'
    assert value['portions'] == 4 and value['minutes'] == 35
    assert value['source_author'] == 'Atelier de test'
    assert value['ingredients'][0]['quantity'] == 200
    assert value['ingredients'][2]['quantity'] is None
    assert 'sel au goût' in value['ingredient_notes']
    assert 'Couper les légumes.' in value['steps'] and 'Faire cuire.' in value['steps']


def test_jsonld_arrays_type_lists_and_entities_inside_json_strings():
    source = structured(name='Plat &quot;maison&quot;', **{'@type': ['Recipe', 'CreativeWork']})
    result = parser.parse_html(source, 'https://public.example')
    assert result['name'] == 'Plat "maison"'
    source = '<script type="application/ld+json">not valid</script>' + source
    assert parser.parse_html(source, 'https://public.example')['method'] == 'jsonld'


def test_generic_html_without_site_specific_selectors():
    value = parser.parse_html('''<main><h1>Gratin de test</h1><h2>Ingrédients</h2><ul>
       <li><span>200</span><span>g</span><span>de pommes de terre</span></li><li>sel</li></ul>
       <h2>Préparation</h2><ol><li>Éplucher.</li><li>Enfourner.</li></ol></main>''', 'https://other.example/gratin')
    assert value['method'] == 'html' and len(value['ingredients']) == 2
    assert value['ingredients'][0]['quantity'] == 200
    assert 'Enfourner.' in value['steps']
    assert value['portions'] is None


def test_microdata_and_plain_paste_keep_unknown_measurements():
    value = parser.parse_html('''<div itemscope itemtype="https://schema.org/Recipe"><h1 itemprop="name">Riz</h1>
      <span itemprop="recipeYield">2 personnes</span><p itemprop="recipeIngredient">100 g de riz</p>
      <div itemprop="recipeInstructions">Cuire le riz.</div></div>''', 'https://public.example')
    assert value['portions'] == 2 and value['ingredients'][0]['name'] == 'riz'
    pasted = parser.parse_text("Riz maison\nPour 2 personnes\nIngrédients :\n100 g de riz\n1 c. à soupe d’huile\nPréparation :\nCuire le riz.")
    assert pasted['portions'] == 2 and len(pasted['ingredients']) == 2
    assert pasted['ingredients'][1]['unit'] is None
    assert 'c. à soupe' in pasted['ingredient_notes']


@pytest.mark.parametrize('raw,quantity,unit', [
    ('250 g de farine', 250, 'g'), ('1,5 kg de pommes de terre', 1.5, 'kg'),
    ('1½ l de lait', 1.5, 'l'), ('1 1 / 2 l de lait', 1.5, 'l'),
    ('25 cl d’huile', 250, 'ml'), ('2 œufs', 2, 'piece'),
    ('sel et poivre', None, None), ('1 c. à soupe d’huile', None, None),
    ('2 à 3 tomates', None, None), ('0 g de sel', None, None),
    ('-5 g de farine', None, None), ('9' * 100 + ' g de farine', None, None),
])
def test_quantities_are_conservative(raw, quantity, unit):
    parsed = parser.parse_ingredient(raw)
    assert parsed['quantity'] == quantity and parsed['unit'] == unit


def test_counts_are_not_automatically_treated_as_persons_and_times_are_combined():
    value = parser.parse_html(structured(recipeYield='Makes 12 pancakes', totalTime='', prepTime='PT10M', cookTime='PT20M'), 'https://public.example')
    assert value['portions'] is None and value['minutes'] == 30
    assert parser.portions('4 à 6 personnes') is None
    assert parser.parse_ingredient('environ 200 g de riz')['needs_review']
    assert parser.duration('1h30') == 90
    assert parser.duration('1h90') is None


def test_a_challenge_page_is_not_presented_as_a_recipe():
    with pytest.raises(ImportProblem):
        parser.parse_html('<html><h1>Access denied</h1><p>Please log in.</p></html>', 'https://public.example')
    with pytest.raises(ImportProblem):
        parser.parse_html('<div>' * 100 + 'deep' + '</div>' * 100, 'https://public.example')


def dashboard(client):
    call(client, 'post', '/weeks', {'start': '2026-11-09'})
    return call(client, 'get', '/dashboard?start=2026-11-09')


def confirmation(items=None):
    return {'operation_id': str(uuid4()), 'recipe': {'name': 'Recette importée de test', 'portions': 4,
        'minutes': 20, 'steps': 'Préparer puis servir.', 'source_url': 'https://public.example/recette',
        'source_author': 'Atelier de test', 'ingredient_notes': 'sel au goût'},
        'items': items or []}


def test_preview_is_authenticated_and_does_not_create_anything(client, monkeypatch):
    monkeypatch.setattr(parser, 'fetch_html', lambda url: (structured(), url))
    before = dashboard(client)
    value = call(client, 'post', '/recipes/import/preview', {'url': 'https://public.example/recette'})
    assert value['source_url'] == 'https://public.example/recette'
    after = dashboard(client)
    for field in ['recipes', 'ingredients', 'stock', 'movements']:
        assert after[field] == before[field]
    csrf = client.headers.pop('X-CSRF-Token')
    call(client, 'post', '/recipes/import/preview', {'url': 'https://public.example'}, expected=403)
    client.headers['X-CSRF-Token'] = csrf


def test_preview_releases_sqlite_before_network_io(client, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    def delayed(*args):
        entered.set()
        assert release.wait(3)
        return {'name': 'Test'}
    monkeypatch.setattr(parser, 'preview', delayed)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(call, client, 'post', '/recipes/import/preview', {'url': 'https://public.example'})
        try:
            assert entered.wait(1)
            second = pool.submit(call, client, 'get', '/settings')
            assert second.result(timeout=1)['portions'] == 4
        finally:
            release.set()
        assert first.result()['name'] == 'Test'


def test_confirmation_creates_recipe_and_normalized_ingredients_once(client):
    body = confirmation([{'name': 'Farine', 'quantity': 200, 'unit': 'g'}])
    first = call(client, 'post', '/recipes/import/confirm', body)
    assert call(client, 'post', '/recipes/import/confirm', body) == first
    value = dashboard(client)
    assert len(value['recipes']) == 1 and len(value['ingredients']) == 1
    assert value['recipes'][0]['source_author'] == 'Atelier de test'
    assert value['recipes'][0]['ingredient_notes'] == 'sel au goût'
    assert not value['stock'] and not value['movements']


def test_invalid_unit_rolls_back_all_new_ingredients_and_recipe(client):
    milk = call(client, 'post', '/ingredients', {'name': 'Lait', 'dimension': 'volume'})['id']
    body = confirmation([{'name': 'Nouveau riz', 'quantity': 200, 'unit': 'g'}, {'ingredient_id': milk, 'quantity': 1, 'unit': 'g'}])
    call(client, 'post', '/recipes/import/confirm', body, expected=422)
    value = dashboard(client)
    assert len(value['ingredients']) == 1 and not value['recipes']


def test_import_preserves_culinary_distinctions_and_old_client_attribution(client):
    call(client, 'post', '/ingredients', {'name': 'pâtes', 'dimension': 'masse'})
    result = call(client, 'post', '/recipes/import/confirm', confirmation([{'name': 'pâtés', 'quantity': 100, 'unit': 'g'}]))
    assert len(dashboard(client)['ingredients']) == 2
    call(client, 'put', f"/recipes/{result['id']}", {'name': 'Renommée', 'kind': 'recette', 'portions': 4})
    recipe = dashboard(client)['recipes'][0]
    assert recipe['source_author'] == 'Atelier de test' and recipe['ingredient_notes'] == 'sel au goût'


def test_additive_migration_preserves_existing_recipes_and_quantities(tmp_path):
    database = tmp_path / 'old.sqlite3'
    backend = Path(__file__).resolve().parents[1]
    config = Config(str(backend / 'alembic.ini'))
    config.set_main_option('script_location', str(backend / 'migrations'))
    config.set_main_option('sqlalchemy.url', 'sqlite:///' + str(database))
    command.upgrade(config, '0001')
    with sqlite3.connect(database) as db:
        db.execute("INSERT INTO ingredients VALUES (1,'Riz','masse')")
        db.execute("INSERT INTO stock VALUES (1,1,'Placard',125000,NULL)")
        db.execute("INSERT INTO recipes (id,name,kind,portions) VALUES (1,'Riz maison','recette',4)")
    migrate(database)
    with sqlite3.connect(database) as db:
        assert db.execute('SELECT quantity FROM stock').fetchone()[0] == 125000
        assert db.execute('SELECT name,source_author,ingredient_notes FROM recipes').fetchone() == ('Riz maison', '', '')
        assert db.execute('SELECT version_num FROM alembic_version').fetchone()[0] == '0006'
