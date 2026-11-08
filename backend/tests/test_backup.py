import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.backup import backup, restore
from app.main import create_app


def test_consistent_live_backup_and_offline_restore_preserve_previous_database(tmp_path):
    path, saved = tmp_path / 'mijote.sqlite3', tmp_path / 'saved.sqlite3'
    with TestClient(create_app(path, secure_cookie=False)) as c:
        r = c.post('/api/v1/auth/setup', json={'name': 'Maison', 'password': 'My-test-password-123'})
        c.headers['X-CSRF-Token'] = r.json()['csrf']
        assert c.post('/api/v1/ingredients', json={'name': 'Riz', 'dimension': 'masse'}).status_code == 200
        backup(path, saved)
        with pytest.raises(ValueError, match='Arrêter'):
            restore(saved, path)
        assert c.post('/api/v1/ingredients', json={'name': 'Farine', 'dimension': 'masse'}).status_code == 200
    restore(saved, path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT name FROM ingredients').fetchall() == [('Riz',)]
    previous = list(tmp_path.glob('pre-restore-*.sqlite3'))
    assert len(previous) == 1
    with sqlite3.connect(previous[0]) as db:
        assert db.execute('SELECT count(*) FROM ingredients').fetchone()[0] == 2


def test_backup_does_not_overwrite_and_restore_rejects_other_files(tmp_path):
    source, target = tmp_path / 'source.sqlite3', tmp_path / 'target.sqlite3'
    with TestClient(create_app(source, secure_cookie=False)):
        backup(source, target)
        with pytest.raises(ValueError, match='existe déjà'):
            backup(source, target)
    invalid = tmp_path / 'other.sqlite3'
    with sqlite3.connect(invalid) as db:
        db.execute('CREATE TABLE unrelated (id)')
    with pytest.raises((ValueError, sqlite3.Error)):
        restore(invalid, target)
    with sqlite3.connect(target) as db:
        assert db.execute('SELECT version_num FROM alembic_version').fetchone()[0] == '0004'
