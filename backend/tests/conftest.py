from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path / 'mijote.sqlite3', secure_cookie=False)
    with TestClient(app) as c:
        result = c.post('/api/v1/auth/setup', json={'name': 'Maison', 'password': 'Un-secret-de-test-123'})
        assert result.status_code == 200, result.text
        c.headers['X-CSRF-Token'] = result.json()['csrf']
        yield c


def call(client, method, path, data=None, expected=200):
    result = client.request(method.upper(), '/api/v1' + path, **({'json': data if data is not None else {}} if method != 'get' else {}))
    assert result.status_code == expected, result.text
    return result.json()


def seed(client, quantity=100, unit='g', portions=4):
    ingredient = call(client, 'post', '/ingredients', {'name': 'Riz basmati', 'dimension': 'masse'})['id']
    recipe = call(client, 'post', '/recipes', {'name': 'Riz aux légumes', 'kind': 'recette', 'portions': portions,
        'ingredients': [{'ingredient_id': ingredient, 'quantity': quantity, 'unit': unit}]})['id']
    meals = call(client, 'post', '/weeks', {'start': '2026-11-09'})['meals']
    return ingredient, recipe, meals


def plan(client, meal, recipe, status='maison', portions=4, side=None):
    return call(client, 'put', f"/meals/{meal['id']}", {'status': status, 'title': '', 'recipe_id': recipe, 'side_id': side, 'portions': portions})
