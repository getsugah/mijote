import json
import sqlite3
from uuid import uuid4

import pytest

from app import ingredients as names
from app.backup import backup, restore
from app.db import connect
from conftest import call, seed, plan


def create(client, name, dimension='masse', **extra):
    return call(client, 'post', '/ingredients', {'name': name, 'dimension': dimension, **extra})['id']


def dashboard(client):
    return call(client, 'get', '/dashboard?start=2026-11-09')


def merge(client, source, target, **extra):
    preview = call(client, 'get', f'/ingredients/{source}/merge-preview?target_id={target}')
    body = {'operation_id': str(uuid4()), 'target_id': target, 'preview_token': preview['token'], **extra}
    return call(client, 'post', f'/ingredients/{source}/merge', body), body


def test_plural_is_proposed_not_silently_created_or_merged(client):
    target = create(client, 'Tomate')
    result = call(client, 'get', '/ingredients/matches?name=tomates&dimension=masse')
    assert [i['id'] for i in result['suggestions']] == [target]
    call(client, 'post', '/ingredients', {'name': 'tomates', 'dimension': 'masse'}, expected=409)
    assert create(client, 'tomates', reuse_id=target) == target
    assert create(client, ' TOMATES ') == target
    assert create(client, 'tomate séchée') != target
    assert create(client, 'sauce tomate') != target
    assert names.plural_key('pâtes') != names.plural_key('pâtés')
    assert names.plural_key('mais') != names.plural_key('mai')


def test_renaming_keeps_references_and_old_spelling_as_alias(client):
    ingredient, recipe, meals = seed(client)
    plan(client, meals[0], recipe)
    call(client, 'post', '/stock', {'ingredient_id': ingredient, 'quantity': 25, 'unit': 'g'})
    call(client, 'put', f'/ingredients/{ingredient}', {'name': 'Riz corrigé', 'dimension': 'masse'})
    assert create(client, 'Riz basmati') == ingredient
    data = dashboard(client)
    assert data['recipes'][0]['ingredients'][0]['ingredient_id'] == ingredient
    assert data['stock'][0]['name'] == 'Riz corrigé'
    assert 'Riz basmati' in data['ingredients'][0]['aliases']
    assert data['shopping']['items'][0]['quantity'] == 75
    call(client, 'put', f'/ingredients/{ingredient}', {'name': 'Riz corrigé', 'dimension': 'volume'}, expected=409)


def test_full_merge_sums_recipe_lines_and_preserves_lots_history_products_courses(client, tmp_path):
    ingredient, recipe, meals = seed(client, quantity=100)
    target = create(client, 'Riz canonique')
    call(client, 'put', f'/recipes/{recipe}', {'name': 'Plat fictif', 'portions': 4, 'ingredients': [
        {'ingredient_id': ingredient, 'quantity': 100, 'unit': 'g'}, {'ingredient_id': target, 'quantity': 0.2, 'unit': 'kg'}]})
    plan(client, meals[0], recipe)
    for ident, amount, location in [(ingredient, 50, 'Placard'), (target, 80, 'Congélateur')]:
        call(client, 'post', '/stock', {'ingredient_id': ident, 'quantity': amount, 'unit': 'g', 'location': location})
        call(client, 'post', '/weeks/2026-11-09/shopping/manual', {'ingredient_id': ident, 'quantity': 10, 'unit': 'g'})
        call(client, 'patch', '/weeks/2026-11-09/shopping/check', {'ingredient_id': ident, 'checked': True})
    with connect(tmp_path / 'mijote.sqlite3') as db:
        db.execute('INSERT INTO products (ingredient_id,name) VALUES (?,?)', (ingredient, 'Produit fictif'))
    before = dashboard(client)
    result, body = merge(client, ingredient, target)
    assert result['id'] == target
    assert call(client, 'post', f'/ingredients/{ingredient}/merge', body) == result
    data = dashboard(client)
    assert [i['id'] for i in data['ingredients']] == [target]
    assert data['recipes'][0]['ingredients'][0]['quantity'] == 300
    assert len(data['recipes'][0]['ingredients']) == 1
    assert [s['id'] for s in data['stock']] == [s['id'] for s in before['stock']]
    assert sum(s['quantity'] for s in data['stock']) == 130
    assert len(data['movements']) == len(before['movements'])
    assert all(s['ingredient_id'] == target for s in data['movements'])
    assert data['shopping']['needs']['items'][0]['required'] == 300
    assert data['shopping']['needs']['items'][0]['missing'] == 170
    assert len([i for i in data['shopping']['items'] if i['manual_id']]) == 2
    assert not next(i for i in data['shopping']['items'] if not i['manual_id'])['checked']
    assert create(client, 'Riz basmati') == target
    with connect(tmp_path / 'mijote.sqlite3') as db:
        assert db.execute('SELECT ingredient_id FROM products').fetchone()[0] == target
        assert not db.execute('PRAGMA foreign_key_check').fetchall()


def test_undo_preparation_after_merge_restores_the_correct_lot(client):
    source, recipe, meals = seed(client)
    target = create(client, 'Riz cible')
    plan(client, meals[0], recipe)
    call(client, 'post', '/stock', {'ingredient_id': source, 'quantity': 100, 'unit': 'g'})
    active = str(uuid4())
    call(client, 'post', f"/meals/{meals[0]['id']}/prepare", {'operation_id': active})
    merge(client, source, target)
    call(client, 'post', f"/meals/{meals[0]['id']}/unprepare", {'operation_id': str(uuid4()), 'preparation_id': active})
    data = dashboard(client)
    assert data['stock'][0]['ingredient_id'] == target and data['stock'][0]['quantity'] == 100
    assert data['shopping']['needs']['items'][0]['ingredient_id'] == target


def test_merge_refuses_stale_preview_incompatible_types_and_missing_confirmation(client):
    source = create(client, 'Tomate')
    target = create(client, 'Tomates', allow_distinct=True)
    volume = create(client, 'Jus de tomate', 'volume')
    call(client, 'get', f'/ingredients/{source}/merge-preview?target_id={volume}', expected=422)
    call(client, 'get', f'/ingredients/{source}/merge-preview?target_id={source}', expected=422)
    preview = call(client, 'get', f'/ingredients/{source}/merge-preview?target_id={target}')
    call(client, 'post', '/stock', {'ingredient_id': source, 'quantity': 10, 'unit': 'g'})
    body = {'operation_id': str(uuid4()), 'target_id': target, 'preview_token': preview['token']}
    call(client, 'post', f'/ingredients/{source}/merge', body, expected=409)
    assert client.post(f'/api/v1/ingredients/{source}/merge', json=body, headers={'X-CSRF-Token': ''}).status_code == 403
    call(client, 'post', f'/ingredients/{source}/merge', {'operation_id': str(uuid4()), 'target_id': target}, expected=422)


def test_old_offline_requests_are_conflicts_and_later_merges_keep_aliases(client):
    source, recipe, meals = seed(client)
    target = create(client, 'Riz cible')
    final = create(client, 'Riz définitif')
    plan(client, meals[0], recipe)
    snapshot = call(client, 'get', '/weeks/2026-11-09/shopping/offline')
    item = snapshot['items'][0]
    merge(client, source, target)
    sync = call(client, 'post', '/shopping/sync', {'household_id': snapshot['household_id'], 'operations': [
        {'operation_id': str(uuid4()), 'week_start': '2026-11-09', 'action': 'check', 'item_key': item['key'], 'expected_version': item['version'], 'checked': True},
        {'operation_id': str(uuid4()), 'week_start': '2026-11-09', 'action': 'add', 'ingredient_id': source, 'quantity': 10, 'unit': 'g'}]})
    assert all(r['status'] == 'conflict' for r in sync['results'])
    merge(client, target, final)
    assert create(client, 'Riz basmati') == final
    assert create(client, 'Riz cible') == final
    call(client, 'put', f'/ingredients/{source}', {'name': 'Ancien lien', 'dimension': 'masse'}, expected=409)


def test_aliases_and_redirects_survive_backup_restore(client, tmp_path):
    source = create(client, 'Tomate')
    target = create(client, 'Tomates', allow_distinct=True)
    merge(client, source, target)
    saved, restored = tmp_path / 'saved.sqlite3', tmp_path / 'restored.sqlite3'
    backup(tmp_path / 'mijote.sqlite3', saved)
    restore(saved, restored)
    with connect(restored) as db:
        assert names.matches(db, 'tomate')['exact'][0]['id'] == target
        assert len(names.listing(db)) == 1
        assert not db.execute('PRAGMA foreign_key_check').fetchall()


def test_existing_import_operation_hashes_remain_replayable(client, tmp_path):
    from test_import import confirmation
    body = confirmation([{'name': 'Farine fictive', 'quantity': 100, 'unit': 'g'}])
    result = call(client, 'post', '/recipes/import/confirm', body)
    # Compatibility: the new false flag must not participate in historical hashes.
    body['items'][0]['allow_distinct'] = False
    assert call(client, 'post', '/recipes/import/confirm', body) == result


def test_import_reuses_confirmed_plural_but_requires_choice_for_new_variant(client):
    from test_import import confirmation
    ident = create(client, 'Tomate')
    call(client, 'post', '/recipes/import/confirm', confirmation([{'name': 'Tomates', 'quantity': 100, 'unit': 'g'}]), expected=409)
    body = confirmation([{'ingredient_id': ident, 'name': 'Tomates', 'quantity': 100, 'unit': 'g'}])
    call(client, 'post', '/recipes/import/confirm', body)
    call(client, 'post', '/recipes/import/confirm', confirmation([{'name': 'Tomates', 'quantity': 200, 'unit': 'g'}]))
    call(client, 'post', '/weeks', {'start': '2026-11-09'})
    assert len(dashboard(client)['ingredients']) == 1
    assert all(r['ingredients'][0]['ingredient_id'] == ident for r in dashboard(client)['recipes'])


def test_canonical_name_can_be_changed_to_a_merged_alias(client):
    source = create(client, 'Tomates')
    target = create(client, 'Tomate', allow_distinct=True)
    merge(client, source, target)
    call(client, 'put', f'/ingredients/{target}', {'name': 'Tomates', 'dimension': 'masse'})
    assert create(client, 'Tomate') == target
    assert create(client, 'Tomates') == target
