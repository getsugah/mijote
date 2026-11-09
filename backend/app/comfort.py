"""Phase B: deterministic inspiration and explicit, non-destructive menu reuse."""
import hashlib
import hmac
import json
from collections import Counter
from datetime import date, timedelta

from fastapi import HTTPException
from . import services as s, meal_items


def record_preparation(db, meal):
    main = s.require(db, 'recipes', meal['recipe_id']) if meal['recipe_id'] else None
    side = s.require(db, 'recipes', meal['side_id']) if meal['side_id'] else None
    details = meal_items.enrich(db, meal)
    additions = meal_items.stored(db, meal['id'])
    db.execute("""INSERT OR IGNORE INTO meal_history VALUES (?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),?,?,?,?,?)""",
               (meal['id'], meal['day'], meal['slot'], meal['recipe_id'], meal['side_id'],
                main['name'] if main else meal['title'] or 'Repas composé', details['side_name'] or '', meal['portions']))
    for item in additions:
        if item['role'] == 'dish':
            db.execute('INSERT INTO meal_history_dishes VALUES (?,?,?,?,?)',
                       (meal['id'], item['position'], item['recipe_id'], meal_items.label(db, item), item['course']))
    for ident in (meal['recipe_id'], meal['side_id'], *[item['recipe_id'] for item in additions]):
        if ident:
            db.execute('UPDATE recipes SET to_try=0 WHERE id=?', (ident,))


def history(db, limit=100, before=None):
    args = []
    where = ''
    if before is not None:
        anchor = db.execute("SELECT COALESCE(prepared_at,planned_day||'T00:00:00.000Z') FROM meal_history WHERE meal_id=?", (before,)).fetchone()
        if anchor is None:
            raise HTTPException(422, 'Curseur d’historique inconnu. Recharger la liste.')
        where = "WHERE (COALESCE(h.prepared_at,h.planned_day||'T00:00:00.000Z'),h.meal_id) < (?,?)"
        args.extend((anchor[0], before))
    args.append(limit)
    # Stable composite cursor: real preparation time, then meal id.
    events = s.rows(db, f'''SELECT h.*,r.rating,r.favorite FROM meal_history h
      LEFT JOIN recipes r ON r.id=h.main_recipe_id {where}
      ORDER BY COALESCE(h.prepared_at,h.planned_day||'T00:00:00.000Z') DESC,h.meal_id DESC LIMIT ?''', args)
    for event in events:
        event['dishes'] = s.rows(db, 'SELECT recipe_id,name,course FROM meal_history_dishes WHERE meal_id=? ORDER BY position', (event['meal_id'],))
    return events


def preferences(db, ident, data):
    s.require(db, 'recipes', ident)
    values = data.model_dump(exclude_unset=True)
    allowed = {'favorite', 'to_try', 'rating', 'category', 'comment', 'variant'}
    if not set(values).issubset(allowed):
        raise HTTPException(422, 'Préférence invalide.')
    db.execute('UPDATE recipes SET ' + ','.join(name + '=?' for name in values) + ' WHERE id=?', (*values.values(), ident))
    return s.require(db, 'recipes', ident)


def suggestions(db, mode, at, portions, excluded):
    if mode not in ('varier', 'stock', 'rapide', 'decouverte'):
        raise HTTPException(422, 'Mode de suggestion inconnu.')
    cooked = s.rows(db, 'SELECT * FROM meal_history')
    last, category_counts = {}, Counter()
    recipes = {r['id']: r for r in s.recipes(db)}
    for event in cooked:
        day = (event['prepared_at'] or event['planned_day'])[:10]
        extra_ids = {r['recipe_id'] for r in db.execute('SELECT recipe_id FROM meal_history_dishes WHERE meal_id=?', (event['meal_id'],))}
        for ident in ({event['main_recipe_id'], event['side_recipe_id']} | extra_ids) - {None}:
            last[ident] = max(last.get(ident, ''), day)
            if ident in recipes and 0 <= (at - date.fromisoformat(day)).days < 14:
                category_counts[recipes[ident]['category']] += 1
    available = {r['ingredient_id']: r['quantity'] for r in s.rows(db,
        'SELECT ingredient_id,SUM(quantity) quantity FROM stock WHERE expires IS NULL OR expires>=? GROUP BY ingredient_id', (at.isoformat(),))}
    expiring = {r['ingredient_id'] for r in s.rows(db, 'SELECT DISTINCT ingredient_id FROM stock WHERE quantity>0 AND expires BETWEEN ? AND ?',
               (at.isoformat(), (at + timedelta(days=7)).isoformat()))}
    planned = Counter()
    for meal in s.rows(db, "SELECT * FROM meals WHERE status='maison' AND prepared=0"):
        for ident, q in s.meal_requirements(db, meal).items():
            available[ident] = max(0, available.get(ident, 0) - q)
        if abs((date.fromisoformat(meal['day']) - at).days) < 7:
            extra_ids = {item['recipe_id'] for item in meal_items.stored(db, meal['id'])}
            for ident in ({meal['recipe_id'], meal['side_id']} | extra_ids) - {None}:
                planned[ident] += 1
    choices = []
    for ident, recipe in recipes.items():
        if ident in excluded or recipe['rating'] == 'ne_plus_proposer':
            continue
        requirements = s.meal_requirements(db, {'recipe_id': ident, 'side_id': None, 'portions': portions})
        covered = sum(available.get(i, 0) >= q for i, q in requirements.items())
        coverage = sum(min(1, available.get(i, 0) / q) for i, q in requirements.items()) / len(requirements) if requirements else 0
        soon = sum(i in expiring and available.get(i, 0) > 0 for i in requirements)
        recent = ident in last and (at - date.fromisoformat(last[ident])).days < 14
        varied = category_counts[recipe['category']] if recipe['category'] != 'autre' else 0
        timing = recipe['minutes'] or 1441
        tie = (planned[ident], -int(recipe['favorite']), last.get(ident, ''), recipe['name'].casefold(), ident)
        if mode == 'stock':
            rank = (-coverage, -soon, recent, varied, *tie)
        elif mode == 'rapide':
            rank = (timing > 30, recent, timing, varied, *tie)
        elif mode == 'decouverte':
            rank = (not recipe['to_try'], ident in last, varied, recent, *tie)
        else:
            rank = (recent, varied, planned[ident], last.get(ident, ''), -int(recipe['favorite']), -coverage, recipe['name'].casefold(), ident)
        reasons = []
        reasons.append('Jamais confirmé comme préparé' if ident not in last else 'Préparé récemment' if recent else 'Pas préparé depuis au moins deux semaines')
        if recipe['minutes']:
            reasons.append(f"{recipe['minutes']} min")
        if requirements:
            reasons.append(f'{covered}/{len(requirements)} ingrédients couverts par les réserves libres')
        else:
            reasons.append('Quantités non renseignées')
        if soon:
            reasons.append(f'{soon} ingrédient(s) à utiliser dans les sept jours')
        if recipe['to_try']:
            reasons.append('À tester')
        if planned[ident]:
            reasons.append('Déjà présent dans les repas planifiés autour de cette date')
        choices.append((rank, {'recipe_id': ident, 'name': recipe['name'], 'category': recipe['category'],
                               'minutes': recipe['minutes'], 'favorite': bool(recipe['favorite']),
                               'last_prepared': last.get(ident), 'reasons': reasons}))
    return [value for _, value in sorted(choices, key=lambda item: item[0])[:8]]


def empty_home(meal, db=None):
    filled = meal_items.has_food(db, meal) if db is not None else any(meal.get(k) for k in ('title', 'recipe_id', 'side_id', 'side_ingredient', 'dishes'))
    return meal['status'] == 'maison' and not meal['prepared'] and not filled


def copy_preview(db, target_start, source_start):
    if target_start == source_start:
        raise HTTPException(422, 'Choisir une autre semaine source.')
    source, target = s.week(db, source_start), s.week(db, target_start)
    values, skipped = [], 0
    for old, new in zip(source['meals'], target['meals']):
        if old['status'] != 'maison' or not meal_items.has_food(db, old) or not empty_home(new, db):
            skipped += 1
            continue
        values.append({'target_id': new['id'], 'day': new['day'], 'slot': new['slot'],
                       'title': old['recipe_name'] or old['title'] or 'Repas composé', 'side_name': old['side_name'], 'dishes': old['dishes'],
                       'source_meal_id': old['id'], 'portions': old['portions']})
    token = hashlib.sha256(json.dumps([source, target], sort_keys=True).encode()).hexdigest()
    return {'items': values, 'skipped': skipped, 'preview_token': token}


def reuse(db, target_id, source_id):
    old, new = s.require(db, 'meals', source_id), s.require(db, 'meals', target_id)
    if not empty_home(new, db):
        raise HTTPException(409, 'Le créneau cible doit être à la maison, vide et non préparé.')
    if not meal_items.has_food(db, old):
        raise HTTPException(422, 'Le repas source ne contient pas de plat.')
    db.execute('UPDATE meals SET title=?,recipe_id=?,side_id=?,portions=? WHERE id=?',
               (old['title'], old['recipe_id'], old['side_id'], old['portions'], target_id))
    meal_items.copy(db, source_id, target_id)


def copy_week(db, target_start, data):
    def perform():
        preview = copy_preview(db, target_start, data.source_start.isoformat())
        if not hmac.compare_digest(preview['preview_token'], data.preview_token):
            raise HTTPException(409, 'Le planning a changé. Revoir l’aperçu avant de copier.')
        for item in preview['items']:
            reuse(db, item['target_id'], item['source_meal_id'])
        return {'copied': len(preview['items']), 'skipped': preview['skipped']}
    return s.operation(db, data, f'copy:{target_start}', perform)
