"""Persistent stock locations, shared by manual entries and purchases."""
import unicodedata

from fastapi import HTTPException


def key(value):
    return unicodedata.normalize('NFKC', value).casefold()


def listing(db):
    return [r['name'] for r in db.execute('SELECT name FROM stock_locations ORDER BY name COLLATE NOCASE')]


def ensure(db, name):
    name = ' '.join(name.split())
    if not name or len(name) > 120:
        raise HTTPException(422, 'Choisir un nom d’emplacement entre 1 et 120 caractères.')
    db.execute('INSERT OR IGNORE INTO stock_locations(name,name_key) VALUES (?,?)', (name, key(name)))
    return db.execute('SELECT name FROM stock_locations WHERE name_key=?', (key(name),)).fetchone()['name']
