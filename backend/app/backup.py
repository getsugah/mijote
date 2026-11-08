"""Consistent SQLite backups and guarded offline restoration. No destructive cleanup."""
import argparse
import fcntl
import os
import sqlite3
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def validate(path):
    with sqlite3.connect(f'file:{path.resolve()}?mode=ro', uri=True) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Sauvegarde SQLite invalide.')
        if db.execute('SELECT version_num FROM alembic_version').fetchone() is None:
            raise ValueError('Version de schéma absente.')
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'users', 'recipes', 'meals', 'stock', 'movements', 'operations'}.issubset(tables):
            raise ValueError('Cette sauvegarde ne correspond pas à Mijote.')


def copy_database(source, destination):
    with sqlite3.connect(f'file:{source.resolve()}?mode=ro', uri=True) as src, sqlite3.connect(destination) as dst:
        src.backup(dst)
    destination.chmod(0o600)


def backup(source, destination):
    if destination.exists():
        raise ValueError('La destination existe déjà ; choisir un autre fichier.')
    validate(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    copy_database(source, destination)
    validate(destination)


def restore(source, destination):
    if source.resolve() == destination.resolve():
        raise ValueError('La sauvegarde et la destination doivent être différentes.')
    validate(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.with_suffix('.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Arrêter Mijote avant de restaurer.') from None
        if destination.exists():
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            previous = destination.with_name(f'pre-restore-{stamp}-{uuid4().hex[:8]}.sqlite3')
            backup(destination, previous)
        copy_database(source, destination)
        validate(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['backup', 'restore'])
    parser.add_argument('file', type=Path)
    args = parser.parse_args()
    database = Path(os.getenv('MIJOTE_DATA_DIR', './data')) / 'mijote.sqlite3'
    try:
        if str(args.file) == '-':
            with tempfile.TemporaryDirectory(prefix='mijote-backup-') as temporary:
                snapshot = Path(temporary) / 'snapshot.sqlite3'
                if args.action == 'backup':
                    backup(database, snapshot)
                    with snapshot.open('rb') as stream:
                        shutil.copyfileobj(stream, sys.stdout.buffer)
                else:
                    with snapshot.open('xb') as stream:
                        shutil.copyfileobj(sys.stdin.buffer, stream)
                    restore(snapshot, database)
                    print('Restauration vérifiée ; ancienne base conservée.')
            return
        if args.action == 'backup':
            backup(database, args.file)
        else:
            restore(args.file, database)
    except (ValueError, sqlite3.Error) as error:
        parser.exit(1, str(error) + '\n')
    print('Sauvegarde vérifiée.' if args.action == 'backup' else 'Restauration vérifiée ; ancienne base conservée.')


if __name__ == '__main__':
    main()
