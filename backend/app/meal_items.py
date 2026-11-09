"""Meal additions shared by planning, needs, history and menu reuse."""
from . import services as s


def stored(db, meal_id):
    return s.rows(db, 'SELECT * FROM meal_dishes WHERE meal_id=? ORDER BY role,position', (meal_id,))


def has_food(db, meal):
    if any(meal.get(k) for k in ('recipe_id', 'title', 'side_id', 'side_ingredient', 'dishes')):
        return True
    return bool(meal.get('id') and db.execute('SELECT 1 FROM meal_dishes WHERE meal_id=?', (meal['id'],)).fetchone())


def label(db, item):
    if item['recipe_id']:
        return s.require(db, 'recipes', item['recipe_id'])['name']
    if item['ingredient_id']:
        ingredient = s.require(db, 'ingredients', item['ingredient_id'])
        amount = f"{item['quantity'] / 1000:g}".replace('.', ',')
        unit = 'pièce(s)' if ingredient['dimension'] == 'piece' else s.BASE_UNITS[ingredient['dimension']]
        return f"{ingredient['name']} · {amount} {unit}"
    return item['title']


def enrich(db, meal):
    result = dict(meal)
    if 'recipe_name' not in result:
        result['recipe_name'] = s.require(db, 'recipes', meal['recipe_id'])['name'] if meal['recipe_id'] else None
        result['side_name'] = s.require(db, 'recipes', meal['side_id'])['name'] if meal['side_id'] else None
    result['dishes'], result['side_ingredient'] = [], None
    for item in stored(db, meal['id']):
        value = {'recipe_id': item['recipe_id'], 'ingredient_id': item['ingredient_id'],
                 'title': item['title'], 'name': label(db, item), 'quantity': None, 'unit': None, 'course': item['course']}
        if item['ingredient_id']:
            ingredient = s.require(db, 'ingredients', item['ingredient_id'])
            value.update(quantity=item['quantity'] / 1000, unit=s.BASE_UNITS[ingredient['dimension']])
        if item['role'] == 'side':
            result['side_ingredient'] = {k: value[k] for k in ('ingredient_id', 'quantity', 'unit')}
            result['side_name'] = value['name']
        else:
            result['dishes'].append(value)
    return result


def save(db, meal_id, data):
    def put(role, position, item):
        recipe_id = getattr(item, 'recipe_id', None)
        ingredient_id = getattr(item, 'ingredient_id', None)
        title = getattr(item, 'title', '')
        if recipe_id:
            s.require(db, 'recipes', recipe_id)
        amount = s.quantity(db, ingredient_id, item.quantity, item.unit) if ingredient_id else None
        db.execute('INSERT INTO meal_dishes VALUES (?,?,?,?,?,?,?,?)',
                   (meal_id, role, position, recipe_id, ingredient_id, title, amount, getattr(item, 'course', 'plat')))
    if 'dishes' in data.model_fields_set:
        db.execute("DELETE FROM meal_dishes WHERE meal_id=? AND role='dish'", (meal_id,))
        for position, item in enumerate(data.dishes):
            put('dish', position, item)
    if 'side_ingredient' in data.model_fields_set or data.side_id:
        db.execute("DELETE FROM meal_dishes WHERE meal_id=? AND role='side'", (meal_id,))
        if data.side_ingredient:
            put('side', 0, data.side_ingredient)


def copy(db, source_id, target_id):
    db.execute('DELETE FROM meal_dishes WHERE meal_id=?', (target_id,))
    db.execute('''INSERT INTO meal_dishes SELECT ?,role,position,recipe_id,ingredient_id,title,quantity,course
                  FROM meal_dishes WHERE meal_id=?''', (target_id, source_id))
