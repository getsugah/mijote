import sqlite3

from fastapi.testclient import TestClient
from app.main import create_app
from conftest import call


def test_auth_csrf_origin_cookie_and_setup_lock(client):
    assert client.get('/api/v1/settings').status_code == 200
    token = client.headers.pop('X-CSRF-Token')
    assert client.post('/api/v1/ingredients', json={'name': 'Sel', 'dimension': 'masse'}).status_code == 403
    client.headers['X-CSRF-Token'] = token
    assert client.post('/api/v1/ingredients', json={'name': 'Sel', 'dimension': 'masse'}, headers={'Origin': 'https://evil.example'}).status_code == 403
    call(client, 'post', '/auth/setup', {'name': 'Autre', 'password': 'Un-autre-secret-123'}, expected=409)
    call(client, 'post', '/auth/logout', {})
    assert client.get('/api/v1/settings').status_code == 401
    result = client.post('/api/v1/auth/login', json={'name': 'Maison', 'password': 'Un-secret-de-test-123'})
    assert result.status_code == 200
    assert 'HttpOnly' in result.headers['set-cookie'] and 'SameSite=lax' in result.headers['set-cookie']
    assert result.headers['cache-control'] == 'no-store'


def test_login_rate_limit(client):
    for _ in range(7):
        assert client.post('/api/v1/auth/login', json={'name': 'Maison', 'password': 'wrong-password-123'}).status_code == 401
    assert client.post('/api/v1/auth/login', json={'name': 'Maison', 'password': 'wrong-password-123'}).status_code == 429


def test_migration_restart_preserves_data_and_password_is_hashed(tmp_path):
    path = tmp_path / 'persistent.sqlite3'
    with TestClient(create_app(path, secure_cookie=False)) as c:
        r = c.post('/api/v1/auth/setup', json={'name': 'Maison', 'password': 'Very-long-secret-123'})
        c.headers['X-CSRF-Token'] = r.json()['csrf']
        call(c, 'post', '/ingredients', {'name': 'Farine', 'dimension': 'masse'})
        cookie = c.cookies.get('mijote_session')
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT password_hash FROM users').fetchone()[0].startswith('scrypt$')
        assert db.execute('SELECT token_hash FROM sessions').fetchone()[0] != cookie
    with TestClient(create_app(path, secure_cookie=False)) as c:
        c.cookies.set('mijote_session', cookie)
        assert c.get('/api/v1/settings').status_code == 200
        with sqlite3.connect(path) as db:
            assert db.execute('SELECT name FROM ingredients').fetchone()[0] == 'Farine'


def test_secure_cookie_for_https_default(tmp_path):
    with TestClient(create_app(tmp_path / 'secure.sqlite3', secure_cookie=True), base_url='https://testserver') as c:
        response = c.post('/api/v1/auth/setup', json={'name': 'Maison', 'password': 'Very-long-secret-123'})
        assert 'Secure' in response.headers['set-cookie']
        assert c.get('/api/v1/auth/me').status_code == 200
