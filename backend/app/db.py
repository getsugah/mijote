import sqlite3
from contextlib import contextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config


def migrate(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    config = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    config.set_main_option('script_location', str(Path(__file__).resolve().parents[1] / 'migrations'))
    config.set_main_option('sqlalchemy.url', ('sqlite:///' + str(path.resolve())).replace('%', '%%'))
    command.upgrade(config, 'head')
    path.chmod(0o600)
    with connect(path) as db:
        for day in range(7):
            for slot in ('midi', 'soir'):
                db.execute('INSERT OR IGNORE INTO presence VALUES (?,?,?)', (day, slot, 'maison'))


@contextmanager
def connect(path: Path):
    db = sqlite3.connect(path, timeout=10, isolation_level=None, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('BEGIN IMMEDIATE')
    try:
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
