"""Transactional household rules. Never deduct stock while planning."""
import hashlib
import json
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException

UNITS = {'g': ('masse', 1000), 'kg': ('masse', 1000000),
         'ml': ('volume', 1000), 'l': ('volume', 1000000), 'piece': ('piece', 1000)}
BASE_UNITS = {'masse': 'g', 'volume': 'ml', 'piece': 'piece'}


def rows(db, sql, args=()):
    return [dict(r) for r in db.execute(sql, args)]


def require(db, table, ident):
    if table not in ('ingredients', 'recipes', 'stock', 'meals', 'shopping_manual'):
        raise ValueError('Invalid repository table')
    row = db.execute(f'SELECT * FROM {table} WHERE id=?', (ident,)).fetchone()
    if row is None:
        raise HTTPException(404, 'Élément introuvable.')
    if table == 'ingredients' and db.execute('SELECT 1 FROM ingredient_redirects WHERE source_id=?', (ident,)).fetchone():
        raise HTTPException(409, 'Cet ingrédient a été fusionné. Rechargez la liste avant de modifier cet article.')
    return dict(row)


def quantity(db, ingredient_id, amount, unit):
    ingredient = require(db, 'ingredients', ingredient_id)
    dimension, factor = UNITS[unit]
    if ingredient['dimension'] != dimension:
        raise HTTPException(422, 'Unité incompatible avec cet ingrédient. Aucune conversion masse/volume automatique.')
    return int(Decimal(str(amount)) * factor)


def display(row):
    item = dict(row)
    if 'quantity' in item:
        item['quantity'] = item['quantity'] / 1000
    if 'delta' in item:
        item['delta'] = item['delta'] / 1000
    if 'dimension' in item:
        item['unit'] = BASE_UNITS[item['dimension']]
    return item


def settings(db):
    return {'portions': db.execute('SELECT portions FROM settings').fetchone()[0],
            'presence': rows(db, 'SELECT * FROM presence ORDER BY day,slot')}


def create_week(db, start: date):
    if start.weekday() != 0:
        raise HTTPException(422, 'La semaine doit commencer un lundi.')
    key = start.isoformat()
    if db.execute('SELECT 1 FROM weeks WHERE start=?', (key,)).fetchone():
        return week(db, key)
    db.execute('INSERT INTO weeks VALUES (?)', (key,))
    model = settings(db)
    for entry in model['presence']:
        day = (start + timedelta(days=entry['day'])).isoformat()
        db.execute('INSERT INTO meals (week_start,day,slot,status,portions) VALUES (?,?,?,?,?)',
                   (key, day, entry['slot'], entry['status'], model['portions']))
    return week(db, key)


def preparation_id(db, ident):
    # Ignore confirmations that merely reported an already-prepared meal.
    for row in db.execute('SELECT id,response FROM operations WHERE kind=? ORDER BY rowid DESC', (f'prepare:{ident}',)):
        if not json.loads(row['response']).get('already_prepared', True):
            return row['id']
    return None


def week(db, key):
    if not db.execute('SELECT 1 FROM weeks WHERE start=?', (key,)).fetchone():
        raise HTTPException(404, 'Créer cette semaine pour appliquer le modèle habituel.')
    meals = rows(db, '''SELECT m.*,r.name AS recipe_name,s.name AS side_name
      FROM meals m LEFT JOIN recipes r ON r.id=m.recipe_id LEFT JOIN recipes s ON s.id=m.side_id
      WHERE week_start=? ORDER BY day,CASE slot WHEN 'midi' THEN 0 ELSE 1 END''', (key,))
    for meal in meals:
        meal['preparation_id'] = preparation_id(db, meal['id']) if meal['prepared'] else None
    from .meal_items import enrich
    return {'start': key, 'meals': [enrich(db, meal) for meal in meals]}


def recipes(db):
    result = rows(db, '''SELECT r.*,p.digest AS photo_version,p.source_url AS photo_source,
      p.attribution AS photo_attribution FROM recipes r LEFT JOIN recipe_photos p ON p.recipe_id=r.id
      ORDER BY r.name COLLATE NOCASE''')
    for recipe in result:
        recipe['ingredients'] = [display(r) for r in rows(db, '''SELECT ri.ingredient_id,ri.quantity,i.name,i.dimension
          FROM recipe_ingredients ri JOIN ingredients i ON i.id=ri.ingredient_id WHERE recipe_id=?''', (recipe['id'],))]
    return result


def save_recipe(db, data, ident=None):
    converted = [(line.ingredient_id, quantity(db, line.ingredient_id, line.quantity, line.unit))
                 for line in data.ingredients]
    author, notes = data.source_author, data.ingredient_notes
    if ident is not None:
        current = require(db, 'recipes', ident)
        if 'source_author' not in data.model_fields_set:
            author = current['source_author']
        if 'ingredient_notes' not in data.model_fields_set:
            notes = current['ingredient_notes']
    fields = (data.name, data.kind, data.portions, data.steps, data.minutes, data.source_url, author, notes)
    if ident is None:
        ident = db.execute('INSERT INTO recipes (name,kind,portions,steps,minutes,source_url,source_author,ingredient_notes) VALUES (?,?,?,?,?,?,?,?)', fields).lastrowid
    else:
        require(db, 'recipes', ident)
        db.execute('UPDATE recipes SET name=?,kind=?,portions=?,steps=?,minutes=?,source_url=?,source_author=?,ingredient_notes=? WHERE id=?', (*fields, ident))
        db.execute('DELETE FROM recipe_ingredients WHERE recipe_id=?', (ident,))
    db.executemany('INSERT INTO recipe_ingredients VALUES (?,?,?)', [(ident, i, q) for i, q in converted])
    return {'id': ident}


def confirm_import(db, data):
    def perform():
        from . import models
        from . import ingredients as catalogue
        created, lines, seen = [], [], set()
        for item in data.items:
            dimension = UNITS[item.unit][0]
            ident = item.ingredient_id
            if ident is None:
                match = catalogue.create(db, item.name, dimension, allow_distinct=item.allow_distinct)
                ident = match['id']
                if not match['reused']:
                    created.append(ident)
            else:
                current = require(db, 'ingredients', ident)
                if item.name and catalogue.plural_key(item.name) == catalogue.plural_key(current['name']):
                    catalogue.alias(db, item.name, ident)
            if ident in seen:
                raise HTTPException(422, 'Regrouper les lignes du même ingrédient avant de confirmer.')
            seen.add(ident)
            quantity(db, ident, item.quantity, item.unit)
            lines.append(models.Line(ingredient_id=ident, quantity=item.quantity, unit=item.unit))
        recipe = data.recipe.model_copy(update={'ingredients': lines})
        saved = save_recipe(db, recipe)
        db.execute('UPDATE recipes SET to_try=1 WHERE id=?', (saved['id'],))
        if data.photo:
            from . import photos
            photos.save(db, saved['id'], photos.from_draft(data.photo), data.photo.source_url, data.photo.attribution)
        return {**saved, 'created_ingredients': len(created)}
    return operation(db, data, 'recipe_import', perform)


def meal_requirements(db, meal):
    from .meal_items import stored
    required = defaultdict(int)
    recipes = [meal['recipe_id'], meal['side_id']]
    if meal.get('id'):
        for item in stored(db, meal['id']):
            if item['recipe_id']:
                recipes.append(item['recipe_id'])
            if item['ingredient_id']:
                required[item['ingredient_id']] += item['quantity']
    for recipe_id in recipes:
        if recipe_id:
            recipe = require(db, 'recipes', recipe_id)
            for row in db.execute('SELECT * FROM recipe_ingredients WHERE recipe_id=?', (recipe_id,)):
                # Round up to the nearest milli-unit, never silently lose a requirement.
                required[row['ingredient_id']] += (row['quantity'] * meal['portions'] + recipe['portions'] - 1) // recipe['portions']
    return required


def needs(db, key):
    week(db, key)
    available = {r['ingredient_id']: r['quantity'] for r in rows(db, 'SELECT ingredient_id,SUM(quantity) quantity FROM stock GROUP BY ingredient_id')}
    totals = defaultdict(lambda: {'required': 0, 'reserved': 0, 'missing': 0})
    per_meal = []
    for meal in rows(db, "SELECT * FROM meals WHERE status='maison' AND prepared=0 ORDER BY day,CASE slot WHEN 'midi' THEN 0 ELSE 1 END,id"):
        lines = []
        for ident, required in meal_requirements(db, meal).items():
            reserved = min(required, available.get(ident, 0))
            available[ident] = available.get(ident, 0) - reserved
            if meal['week_start'] == key:
                value = totals[ident]
                value['required'] += required
                value['reserved'] += reserved
                value['missing'] += required - reserved
                lines.append({'ingredient_id': ident, 'required': required / 1000,
                              'reserved': reserved / 1000, 'missing': (required - reserved) / 1000})
        if meal['week_start'] == key:
            per_meal.append({'meal_id': meal['id'], 'ingredients': lines})
    items = []
    for ident, values in totals.items():
        ingredient = require(db, 'ingredients', ident)
        items.append({'ingredient_id': ident, 'name': ingredient['name'], 'unit': BASE_UNITS[ingredient['dimension']],
                      **{field: value / 1000 for field, value in values.items()}})
    return {'items': sorted(items, key=lambda x: x['name'].casefold()), 'meals': per_meal}


def shopping(db, key):
    computed = needs(db, key)
    checked = {r['ingredient_id']: bool(r['checked']) for r in rows(db, 'SELECT * FROM shopping_checks WHERE week_start=?', (key,))}
    items = [{'key': f"auto-{i['ingredient_id']}", 'manual_id': None, 'ingredient_id': i['ingredient_id'],
              'name': i['name'], 'unit': i['unit'], 'quantity': i['missing'],
              'checked': checked.get(i['ingredient_id'], False)} for i in computed['items'] if i['missing'] > 0]
    for r in rows(db, '''SELECT s.*,i.name,i.dimension FROM shopping_manual s JOIN ingredients i ON i.id=s.ingredient_id
                        WHERE s.week_start=? AND purchased=0 ORDER BY s.id''', (key,)):
        item = display(r)
        items.append({'key': f"manual-{r['id']}", 'manual_id': r['id'], 'ingredient_id': r['ingredient_id'],
                      'name': r['name'], 'unit': item['unit'], 'quantity': item['quantity'], 'checked': bool(r['checked'])})
    return {'items': items, 'needs': computed}


def stock(db):
    return [display(r) for r in rows(db, '''SELECT s.*,i.name,i.dimension FROM stock s JOIN ingredients i ON i.id=s.ingredient_id
       ORDER BY CASE WHEN expires IS NULL THEN 1 ELSE 0 END,expires,s.id''')]


def movement(db, ident, lot, delta, reason, operation=None):
    db.execute('INSERT INTO movements (ingredient_id,stock_id,delta,reason,operation_id) VALUES (?,?,?,?,?)',
               (ident, lot, delta, reason, operation))


def add_stock(db, line, reason='Entrée manuelle', operation=None):
    q = quantity(db, line.ingredient_id, line.quantity, line.unit)
    lot = db.execute('INSERT INTO stock (ingredient_id,location,quantity,expires) VALUES (?,?,?,?)',
                     (line.ingredient_id, line.location, q, line.expires.isoformat() if line.expires else None)).lastrowid
    movement(db, line.ingredient_id, lot, q, reason, operation)
    return {'id': lot}


def operation(db, data, kind, perform):
    ident = str(data.operation_id)
    body = data.model_dump(mode='json')
    # Preserve replay hashes for imports confirmed before photos were introduced.
    if kind == 'recipe_import' and body.get('photo') is None:
        body.pop('photo', None)
    if kind == 'recipe_import':
        for item in body.get('items', []):
            if not item.get('allow_distinct'):
                item.pop('allow_distinct', None)
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    prior = db.execute('SELECT * FROM operations WHERE id=?', (ident,)).fetchone()
    if prior:
        if prior['kind'] != kind or prior['request_hash'] != digest:
            raise HTTPException(409, 'Cet identifiant de confirmation a déjà servi à une autre action.')
        return json.loads(prior['response'])
    result = perform()
    db.execute('INSERT INTO operations VALUES (?,?,?,?)', (ident, kind, digest, json.dumps(result)))
    return result


def prepare(db, ident, data):
    def perform():
        meal = require(db, 'meals', ident)
        if meal['prepared']:
            return {'prepared': True, 'already_prepared': True, 'shortages': []}
        if meal['status'] != 'maison':
            raise HTTPException(409, 'Seul un repas à la maison peut être confirmé.')
        from .meal_items import has_food
        if not has_food(db, meal):
            raise HTTPException(422, 'Choisir un plat avant de confirmer le repas.')
        required = meal_requirements(db, meal)
        if data.quantities is not None:
            provided = {line.ingredient_id: quantity(db, line.ingredient_id, line.quantity, line.unit) for line in data.quantities}
            if any(i not in required for i in provided):
                raise HTTPException(422, 'La correction doit concerner les ingrédients de ce repas.')
            # An omitted ingredient explicitly means no consumption, not the planned quantity.
            required = provided
        shortages = []
        for ingredient_id, requested in required.items():
            remaining = requested
            for lot in rows(db, '''SELECT * FROM stock WHERE ingredient_id=? AND quantity>0
                 ORDER BY CASE WHEN expires IS NULL THEN 1 ELSE 0 END,expires,id''', (ingredient_id,)):
                used = min(lot['quantity'], remaining)
                if used:
                    db.execute('UPDATE stock SET quantity=quantity-? WHERE id=?', (used, lot['id']))
                    movement(db, ingredient_id, lot['id'], -used, f'Repas {ident} préparé', str(data.operation_id))
                    remaining -= used
                if not remaining:
                    break
            if remaining:
                ingredient = require(db, 'ingredients', ingredient_id)
                shortages.append({'ingredient_id': ingredient_id, 'name': ingredient['name'],
                                  'quantity': remaining / 1000, 'unit': BASE_UNITS[ingredient['dimension']]})
        from .comfort import record_preparation
        record_preparation(db, meal)
        db.execute('UPDATE meals SET prepared=1 WHERE id=?', (ident,))
        return {'prepared': True, 'already_prepared': False, 'shortages': shortages}
    return operation(db, data, f'prepare:{ident}', perform)


def unprepare(db, ident, data):
    def perform():
        meal = require(db, 'meals', ident)
        if not meal['prepared']:
            return {'prepared': False, 'already_unprepared': True, 'restored': []}
        active = preparation_id(db, ident)
        if not active:
            raise HTTPException(409, 'La confirmation d’origine de ce repas est introuvable. Aucune quantité ne peut être rétablie automatiquement ; vérifier le journal des réserves.')
        if str(data.preparation_id) != active:
            raise HTTPException(409, 'Ce repas a été préparé à nouveau depuis l’ouverture. Recharger avant d’annuler sa préparation.')
        restored = []
        for entry in rows(db, '''SELECT ingredient_id,stock_id,SUM(-delta) quantity FROM movements
             WHERE operation_id=? AND delta<0 GROUP BY ingredient_id,stock_id''', (active,)):
            changed = db.execute('UPDATE stock SET quantity=quantity+? WHERE id=? AND ingredient_id=?',
                                 (entry['quantity'], entry['stock_id'], entry['ingredient_id']))
            if changed.rowcount != 1:
                raise HTTPException(409, 'Un lot consommé est introuvable. Aucune annulation partielle n’a été appliquée.')
            movement(db, entry['ingredient_id'], entry['stock_id'], entry['quantity'],
                     f'Annulation de la préparation du repas {ident}', str(data.operation_id))
            ingredient = require(db, 'ingredients', entry['ingredient_id'])
            restored.append({'ingredient_id': entry['ingredient_id'], 'stock_id': entry['stock_id'],
                             'quantity': entry['quantity'] / 1000, 'unit': BASE_UNITS[ingredient['dimension']]})
        # The stock journal and operation records retain the cancellation audit.
        db.execute('DELETE FROM meal_history WHERE meal_id=?', (ident,))
        db.execute('UPDATE meals SET prepared=0 WHERE id=?', (ident,))
        return {'prepared': False, 'already_unprepared': False, 'restored': restored}
    return operation(db, data, f'unprepare:{ident}', perform)


def purchase(db, key, data):
    def perform():
        current = shopping(db, key)['items']
        selected = {item['key']: item for item in current}
        seen = set()
        for line in data.items:
            target = f'manual-{line.manual_id}' if line.manual_id else f'auto-{line.requested_ingredient_id or line.ingredient_id}'
            if target in seen:
                raise HTTPException(422, 'Un article ne peut être confirmé qu’une fois.')
            seen.add(target)
            if target not in selected or not selected[target]['checked']:
                raise HTTPException(409, 'La liste a changé ou cet article n’est plus dans le panier. Actualiser avant de confirmer.')
            add_stock(db, line, 'Courses terminées', str(data.operation_id))
            if line.manual_id:
                db.execute('UPDATE shopping_manual SET purchased=1,checked=0 WHERE id=?', (line.manual_id,))
            else:
                original = line.requested_ingredient_id or line.ingredient_id
                db.execute('UPDATE shopping_checks SET checked=0 WHERE week_start=? AND ingredient_id=?', (key, original))
        return {'purchased': len(data.items)}
    return operation(db, data, f'purchase:{key}', perform)
