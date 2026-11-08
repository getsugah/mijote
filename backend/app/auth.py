import hashlib
import hmac
import secrets
import time

from fastapi import HTTPException


def password_hash(password: str):
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=32768, r=8, p=3, maxmem=64 * 1024 * 1024)
    return f'scrypt$32768$8$3${salt}${digest.hex()}'


def password_matches(password: str, stored: str):
    parts = stored.split('$')
    if len(parts) == 3:  # Keep first development databases usable.
        _, salt, expected = parts
        n, r, p = 32768, 8, 1
    else:
        _, n, r, p, salt, expected = parts
        n, r, p = int(n), int(r), int(p)
    actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=n, r=r, p=p, maxmem=64 * 1024 * 1024)
    return hmac.compare_digest(actual.hex(), expected)


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def session(db, token):
    row = db.execute('SELECT * FROM sessions WHERE token_hash=? AND expires>?', (token_hash(token or ''), int(time.time()))).fetchone()
    if row is None:
        raise HTTPException(401, 'Connexion nécessaire.')
    return dict(row)


def new_session(db, response, secure):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    lifetime = 7 * 86400
    db.execute('DELETE FROM sessions WHERE expires<=?', (int(time.time()),))
    db.execute('INSERT INTO sessions VALUES (?,1,?,?)', (token_hash(token), csrf, int(time.time()) + lifetime))
    response.set_cookie('mijote_session', token, max_age=lifetime, httponly=True, secure=secure, samesite='lax', path='/')
    from .offline_shopping import household_id
    return {'name': db.execute('SELECT name FROM users WHERE id=1').fetchone()[0], 'csrf': csrf, 'household_id': household_id(db)}
