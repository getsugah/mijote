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


def change(db, original, name, remove=False):
    row = db.execute('SELECT * FROM stock_locations WHERE name=?', (original,)).fetchone()
    if row is None:
        raise HTTPException(404, 'Emplacement introuvable. Actualisez la liste.')
    name = ' '.join(name.split())
    if not name or len(name) > 120:
        raise HTTPException(422, 'Choisir un nom d’emplacement entre 1 et 120 caractères.')
    target = db.execute('SELECT * FROM stock_locations WHERE name_key=?', (key(name),)).fetchone()
    if remove:
        if target is None or target['id'] == row['id']:
            raise HTTPException(422, 'Choisir un autre emplacement pour conserver les articles et leur historique.')
        name = target['name']
    else:
        if target is not None and target['id'] != row['id']:
            raise HTTPException(409, 'Un emplacement porte déjà ce nom.')
        db.execute('UPDATE stock_locations SET name=?,name_key=? WHERE id=?', (name, key(name), row['id']))
    db.execute('UPDATE stock SET location=? WHERE location=?', (name, original))
    if remove:
        db.execute('DELETE FROM stock_locations WHERE id=?', (row['id'],))
    return {'name': name}
