"""On-demand combined shopping; original weeks and their items remain intact."""
import hashlib
import json
from decimal import Decimal

from fastapi import HTTPException
from . import services as s


def selection(db, weeks):
    keys = [day.isoformat() for day in weeks]
    grouped = {}
    for key in keys:
        for item in s.shopping(db, key)['items']:
            ident = item['ingredient_id']
            if ident not in grouped:
                grouped[ident] = {'key': f'selection-{ident}', 'ingredient_id': ident, 'name': item['name'],
                                  'unit': item['unit'], 'manual_id': None, 'sources': [], '_quantity': 0}
            group = grouped[ident]
            group['_quantity'] += int(Decimal(str(item['quantity'])) * 1000)
            group['sources'].append({'week_start': key, **item})
    items = []
    for group in grouped.values():
        group['quantity'] = group.pop('_quantity') / 1000
        group['checked'] = all(item['checked'] for item in group['sources'])
        group['partially_checked'] = any(item['checked'] for item in group['sources']) and not group['checked']
        group['version'] = hashlib.sha256(json.dumps(group['sources'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        items.append(group)
    return {'weeks': keys, 'items': sorted(items, key=lambda item: item['name'].casefold())}


def current_item(items, ident, version):
    item = next((item for item in items if item['ingredient_id'] == ident), None)
    if item is None or item['version'] != version:
        raise HTTPException(409, 'La liste regroupée a changé. Recharger avant de confirmer.')
    return item


def set_checked(db, item, checked):
    for source in item['sources']:
        if source['manual_id']:
            db.execute('UPDATE shopping_manual SET checked=? WHERE id=?', (checked, source['manual_id']))
        else:
            db.execute('INSERT INTO shopping_checks VALUES (?,?,?) ON CONFLICT(week_start,ingredient_id) DO UPDATE SET checked=excluded.checked',
                       (source['week_start'], source['ingredient_id'], checked))


def check(db, data):
    item = current_item(selection(db, data.weeks)['items'], data.ingredient_id, data.version)
    set_checked(db, item, data.checked)
    return {'ok': True}


def purchase(db, data):
    def perform():
        current = selection(db, data.weeks)['items']
        selected, seen = [], set()
        for line in data.items:
            if line.requested_ingredient_id in seen:
                raise HTTPException(422, 'Un article ne peut être confirmé qu’une fois.')
            seen.add(line.requested_ingredient_id)
            item = current_item(current, line.requested_ingredient_id, line.version)
            if not item['checked']:
                raise HTTPException(409, 'Cet article n’est plus entièrement dans le panier.')
            s.quantity(db, line.ingredient_id, line.quantity, line.unit)
            selected.append((line, item))
        for line, item in selected:
            if line.found:
                s.add_stock(db, line, 'Courses regroupées terminées', str(data.operation_id))
                for source in item['sources']:
                    if source['manual_id']:
                        db.execute('UPDATE shopping_manual SET purchased=1 WHERE id=?', (source['manual_id'],))
            set_checked(db, item, False)
        return {'purchased': sum(line.found for line, _ in selected)}
    return s.operation(db, data, 'purchase-selection', perform)
