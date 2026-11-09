"""Versioned, idempotent shopping sync. These operations never modify physical stock."""
import hashlib
import hmac
import json
from datetime import datetime, timezone

from fastapi import HTTPException
from . import services as s


def household_id(db):
    return db.execute("SELECT value FROM app_meta WHERE key='household_id'").fetchone()[0]


def version(db, week, item):
    counter = db.execute('SELECT revision FROM shopping_revisions WHERE week_start=? AND item_key=?', (week, item['key'])).fetchone()
    value = [week, dict(item), counter[0] if counter else 0]
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def snapshot(db, week):
    from .ingredients import listing
    current = s.shopping(db, week)
    return {'household_id': household_id(db), 'week_start': week,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'ingredients': listing(db),
            'items': [{**item, 'version': version(db, week, item)} for item in current['items']]}


def apply_one(db, operation):
    week = operation.week_start.isoformat()
    s.week(db, week)
    if operation.action == 'add':
        q = s.quantity(db, operation.ingredient_id, operation.quantity, operation.unit)
        ident = db.execute('INSERT INTO shopping_manual (week_start,ingredient_id,quantity,checked) VALUES (?,?,?,?)',
                           (week, operation.ingredient_id, q, operation.checked)).lastrowid
        return {'created_key': f'manual-{ident}'}
    item = next((item for item in s.shopping(db, week)['items'] if item['key'] == operation.item_key), None)
    if item is None:
        raise HTTPException(409, 'Cet article a disparu ou ses besoins ont été satisfaits sur le serveur.')
    if not hmac.compare_digest(version(db, week, item), operation.expected_version):
        raise HTTPException(409, 'Cet article a changé sur un autre appareil. Vérifier la version actuelle avant de réappliquer.')
    if operation.action == 'check':
        if item['manual_id']:
            db.execute('UPDATE shopping_manual SET checked=? WHERE id=?', (operation.checked, item['manual_id']))
        else:
            db.execute('INSERT INTO shopping_checks VALUES (?,?,?) ON CONFLICT(week_start,ingredient_id) DO UPDATE SET checked=excluded.checked',
                       (week, item['ingredient_id'], operation.checked))
    elif operation.action == 'edit':
        if not item['manual_id']:
            raise HTTPException(422, 'Les quantités calculées se modifient depuis les repas.')
        q = s.quantity(db, item['ingredient_id'], operation.quantity, operation.unit)
        db.execute('UPDATE shopping_manual SET quantity=?,checked=? WHERE id=?', (q, operation.checked, item['manual_id']))
    elif operation.action == 'remove':
        if not item['manual_id']:
            raise HTTPException(422, 'Un besoin calculé ne peut pas être supprimé manuellement.')
        db.execute('DELETE FROM shopping_manual WHERE id=?', (item['manual_id'],))
    return {'updated_key': operation.item_key}


def sync(db, data):
    if str(data.household_id) != household_id(db):
        raise HTTPException(409, 'Cette copie de courses appartient à une autre maison. Aucun changement envoyé.')
    result = []
    for operation in data.operations:
        db.execute('SAVEPOINT shopping_sync')
        try:
            response = s.operation(db, operation, 'offline:' + operation.week_start.isoformat(), lambda: apply_one(db, operation))
            db.execute('RELEASE shopping_sync')
            result.append({'operation_id': str(operation.operation_id), 'status': 'applied', **response})
        except HTTPException as error:
            db.execute('ROLLBACK TO shopping_sync')
            db.execute('RELEASE shopping_sync')
            result.append({'operation_id': str(operation.operation_id),
                           'status': 'conflict' if error.status_code in (404, 409) else 'invalid', 'message': error.detail})
    return {'results': result}
