"""Conservative suggestions and explicitly confirmed ingredient merges."""
import hashlib
import hmac
import json
import unicodedata

from fastapi import HTTPException
from . import services as s


def normalized(name):
    return ' '.join(unicodedata.normalize('NFKC', name).casefold().replace('’', "'").split())


def plural_key(name):
    # A suggestion only, never an automatic equivalence. Keep accents/qualifiers.
    def word(value):
        if value == 'choux':
            return 'chou'
        if len(value) > 3 and value.endswith('s') and not value.endswith(('ss', 'us', 'is', 'as', 'os')):
            return value[:-1]
        return value
    return ' '.join(word(value) for value in normalized(name).split())


def listing(db):
    items = s.rows(db, '''SELECT i.* FROM ingredients i LEFT JOIN ingredient_redirects r ON r.source_id=i.id
                         WHERE r.source_id IS NULL ORDER BY i.name COLLATE NOCASE''')
    aliases = {}
    for row in db.execute('SELECT ingredient_id,display_name FROM ingredient_aliases ORDER BY name'):
        aliases.setdefault(row['ingredient_id'], []).append(row['display_name'])
    return [{**item, 'aliases': aliases.get(item['id'], [])} for item in items]


def matches(db, name, dimension=None):
    exact, suggestions = [], []
    for item in listing(db):
        names = [item['name'], *item['aliases']]
        if any(normalized(n) == normalized(name) for n in names):
            exact.append(item)
        elif (dimension is None or item['dimension'] == dimension) and any(plural_key(n) == plural_key(name) for n in names):
            suggestions.append(item)
    return {'exact': exact, 'suggestions': suggestions}


def alias(db, name, ident):
    found = matches(db, name)['exact']
    if any(item['id'] != ident for item in found):
        raise HTTPException(409, 'Ce nom correspond à un autre ingrédient. Utilisez la fusion pour les réunir.')
    db.execute('INSERT INTO ingredient_aliases VALUES (?,?,?) ON CONFLICT(name) DO UPDATE SET ingredient_id=excluded.ingredient_id',
               (normalized(name), name, ident))


def create(db, name, dimension, reuse_id=None, allow_distinct=False):
    found = matches(db, name, dimension)
    if reuse_id:
        current = s.require(db, 'ingredients', reuse_id)
        if current['dimension'] != dimension:
            raise HTTPException(422, 'Les types de mesure doivent être identiques.')
        if not any(i['id'] == reuse_id for i in found['exact'] + found['suggestions']):
            raise HTTPException(409, 'Cette proposition a changé. Vérifiez le nom avant de réutiliser un ingrédient.')
        alias(db, name, reuse_id)
        return {**current, 'reused': True}
    if len(found['exact']) > 1:
        raise HTTPException(409, 'Plusieurs ingrédients correspondent à ce nom. Fusionnez les doublons après vérification.')
    if found['exact']:
        current = found['exact'][0]
        if current['dimension'] != dimension:
            raise HTTPException(409, 'Un ingrédient du même nom utilise un autre type d’unité. Corrigez le nom ou la mesure.')
        return {**current, 'reused': True}
    if found['suggestions'] and not allow_distinct:
        raise HTTPException(409, 'Un ingrédient proche existe déjà. Choisissez « Utiliser » ou confirmez la création d’un ingrédient distinct.')
    ident = db.execute('INSERT INTO ingredients (name,dimension) VALUES (?,?)', (name, dimension)).lastrowid
    return {**s.require(db, 'ingredients', ident), 'reused': False}


def rename(db, ident, data):
    current = s.require(db, 'ingredients', ident)
    if any(i['id'] != ident for i in matches(db, data.name)['exact']):
        raise HTTPException(409, 'Ce nom est déjà utilisé. Fusionnez les deux ingrédients au lieu de supprimer celui qui est utilisé.')
    if current['dimension'] != data.dimension:
        used = db.execute('''SELECT 1 FROM recipe_ingredients WHERE ingredient_id=? UNION ALL
          SELECT 1 FROM stock WHERE ingredient_id=? UNION ALL SELECT 1 FROM shopping_manual WHERE ingredient_id=?
          UNION ALL SELECT 1 FROM movements WHERE ingredient_id=? UNION ALL SELECT 1 FROM products WHERE ingredient_id=?''', (ident,)*5).fetchone()
        if used:
            raise HTTPException(409, 'Un ingrédient utilisé conserve son type d’unité.')
    alias(db, current['name'], ident)
    db.execute('UPDATE ingredients SET name=?,dimension=? WHERE id=?', (data.name, data.dimension, ident))
    return s.require(db, 'ingredients', ident)


def merge_preview(db, source_id, target_id):
    if source_id == target_id:
        raise HTTPException(422, 'Choisissez deux ingrédients différents.')
    source, target = (s.require(db, 'ingredients', ident) for ident in (source_id, target_id))
    if source['dimension'] != target['dimension']:
        raise HTTPException(422, 'La fusion exige le même type de mesure : poids, volume ou pièces.')
    references = {}
    for table in ('recipe_ingredients', 'stock', 'movements', 'products', 'shopping_manual', 'shopping_checks', 'ingredient_aliases'):
        references[table] = s.rows(db, f'SELECT * FROM {table} WHERE ingredient_id IN (?,?) ORDER BY rowid', (source_id, target_id))
    redirects = s.rows(db, 'SELECT * FROM ingredient_redirects WHERE target_id IN (?,?) ORDER BY source_id', (source_id, target_id))
    token = hashlib.sha256(json.dumps([source, target, references, redirects], sort_keys=True).encode()).hexdigest()
    return {'source': source, 'target': target, 'token': token,
            'counts': {table: len(values) for table, values in references.items()}}


def merge(db, source_id, data):
    def perform():
        preview = merge_preview(db, source_id, data.target_id)
        if not hmac.compare_digest(preview['token'], data.preview_token):
            raise HTTPException(409, 'Les données ont changé. Relisez l’aperçu avant de confirmer la fusion.')
        target_id = data.target_id
        db.execute('''INSERT INTO recipe_ingredients (recipe_id,ingredient_id,quantity)
          SELECT recipe_id,?,quantity FROM recipe_ingredients WHERE ingredient_id=?
          ON CONFLICT(recipe_id,ingredient_id) DO UPDATE SET quantity=quantity+excluded.quantity''', (target_id, source_id))
        db.execute('DELETE FROM recipe_ingredients WHERE ingredient_id=?', (source_id,))
        # Keep lots, dates, movement IDs and manual shopping lines separate.
        for table in ('stock', 'movements', 'products', 'shopping_manual'):
            db.execute(f'UPDATE {table} SET ingredient_id=? WHERE ingredient_id=?', (target_id, source_id))
        checks = s.rows(db, 'SELECT * FROM shopping_checks WHERE ingredient_id=?', (source_id,))
        for check in checks:
            # A changed calculated quantity needs checking again before purchasing.
            db.execute('INSERT INTO shopping_checks VALUES (?,?,0) ON CONFLICT(week_start,ingredient_id) DO UPDATE SET checked=0',
                       (check['week_start'], target_id))
        db.execute('UPDATE shopping_checks SET checked=0 WHERE ingredient_id=?', (target_id,))
        db.execute('DELETE FROM shopping_checks WHERE ingredient_id=?', (source_id,))
        db.execute('UPDATE ingredient_aliases SET ingredient_id=? WHERE ingredient_id=?', (target_id, source_id))
        db.execute('UPDATE ingredient_redirects SET target_id=? WHERE target_id=?', (target_id, source_id))
        db.execute('INSERT INTO ingredient_redirects VALUES (?,?)', (source_id, target_id))
        alias(db, preview['source']['name'], target_id)
        # Free the former unique display name while retaining the historical ID.
        db.execute('UPDATE ingredients SET name=? WHERE id=?',
                   (f'Fusion {source_id} {data.operation_id}', source_id))
        return {'id': target_id, 'name': preview['target']['name'], 'merged_id': source_id}
    return s.operation(db, data, f'ingredient_merge:{source_id}', perform)
