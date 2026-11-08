import hmac
import fcntl
import os
import sqlite3
import threading
import time
import re
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from . import auth, models as m, services as s
from .db import connect, migrate


def create_app(db_path: Path | None = None, secure_cookie: bool | None = None):
    path = db_path or Path(os.getenv('MIJOTE_DATA_DIR', './data')) / 'mijote.sqlite3'
    secure = secure_cookie if secure_cookie is not None else os.getenv('MIJOTE_SECURE_COOKIE', 'true').lower() == 'true'
    origins = {x.strip().rstrip('/') for x in os.getenv('MIJOTE_ALLOWED_ORIGINS', 'http://localhost:8080,http://127.0.0.1:8080').split(',') if x.strip()}
    failures: dict[str, list[float]] = {}
    rate_lock = threading.Lock()
    dummy_hash = auth.password_hash('unusable-placeholder-password')

    @asynccontextmanager
    async def lifespan(app):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_SH)
            migrate(path)
            yield

    app = FastAPI(title='Mijote', version='0.5.0', lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware('http')
    async def protections(request: Request, call_next):
        if request.url.path.startswith('/api/') and request.method not in ('GET', 'HEAD', 'OPTIONS'):
            photo_upload = request.method == 'PUT' and bool(re.fullmatch(r'/api/v1/recipes/[1-9][0-9]*/photo', request.url.path))
            origin = request.headers.get('origin')
            if origin and origin.rstrip('/') not in origins:
                return JSONResponse({'detail': 'Origine non autorisée.'}, status_code=403)
            try:
                if int(request.headers.get('content-length', '0')) > (12 * 1024 * 1024 if photo_upload else 1024 * 1024):
                    return JSONResponse({'detail': 'Requête trop volumineuse.'}, status_code=413)
            except ValueError:
                return JSONResponse({'detail': 'Requête invalide.'}, status_code=400)
            if not photo_upload and request.headers.get('content-type', '').split(';')[0] != 'application/json':
                return JSONResponse({'detail': 'Envoyer du JSON.'}, status_code=415)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer' if request.url.path == '/share-recipe' else 'same-origin'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        if request.url.path.startswith('/api/') or request.url.path == '/share-recipe':
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(sqlite3.IntegrityError)
    async def constraint(request, error):
        return JSONResponse({'detail': 'Cet élément existe déjà ou est encore utilisé.'}, status_code=409)

    def database():
        with connect(path) as db:
            yield db

    def authenticated(request: Request, db=Depends(database)):
        value = auth.session(db, request.cookies.get('mijote_session'))
        if request.method not in ('GET', 'HEAD') and not hmac.compare_digest(value['csrf'], request.headers.get('x-csrf-token', '')):
            raise HTTPException(403, 'Confirmation de session invalide. Recharger la page.')
        return value

    def preview_access(request: Request):
        # Do not hold the household's SQLite write transaction during network I/O.
        with connect(path) as db:
            return authenticated(request, db)

    def guard_attempt(request):
        ip = request.client.host if request.client else 'unknown'
        with rate_lock:
            now = time.monotonic()
            # Bound memory and allow retries after a quiet period.
            for key in list(failures):
                failures[key] = [t for t in failures[key] if now - t < 900]
                if not failures[key]:
                    del failures[key]
            attempts = failures.setdefault(ip, [])
            if len(attempts) >= 8:
                raise HTTPException(429, 'Trop de tentatives. Réessayer dans quinze minutes.')
            attempts.append(now)
        return ip

    @app.get('/api/v1/health')
    def health(db=Depends(database)):
        db.execute('SELECT version_num FROM alembic_version').fetchone()
        return {'status': 'ok'}

    @app.get('/api/v1/auth/status')
    def auth_status(db=Depends(database)):
        return {'initialized': bool(db.execute('SELECT 1 FROM users').fetchone())}

    @app.post('/api/v1/auth/setup')
    def setup(data: m.Credentials, request: Request, response: Response, db=Depends(database)):
        guard_attempt(request)
        if db.execute('SELECT 1 FROM users').fetchone():
            raise HTTPException(409, 'Le compte familial existe déjà.')
        db.execute('INSERT INTO users VALUES (1,?,?)', (data.name, auth.password_hash(data.password)))
        return auth.new_session(db, response, secure)

    @app.post('/api/v1/auth/login')
    def login(data: m.Credentials, request: Request, response: Response, db=Depends(database)):
        ip = guard_attempt(request)
        user = db.execute('SELECT * FROM users WHERE id=1').fetchone()
        valid = auth.password_matches(data.password, user['password_hash'] if user else dummy_hash)
        if not user or not valid or data.name != user['name']:
            raise HTTPException(401, 'Nom ou mot de passe incorrect.')
        with rate_lock:
            failures.pop(ip, None)
        return auth.new_session(db, response, secure)

    @app.get('/api/v1/auth/me')
    def me(value=Depends(authenticated), db=Depends(database)):
        from .offline_shopping import household_id
        return {'name': db.execute('SELECT name FROM users').fetchone()[0], 'csrf': value['csrf'], 'household_id': household_id(db)}

    @app.post('/api/v1/auth/logout')
    def logout(response: Response, value=Depends(authenticated), db=Depends(database)):
        db.execute('DELETE FROM sessions WHERE token_hash=?', (value['token_hash'],))
        response.delete_cookie('mijote_session', path='/', secure=secure, httponly=True, samesite='lax')
        return {'ok': True}

    api = '/api/v1'
    access = [Depends(authenticated)]

    @app.get(api + '/settings', dependencies=access)
    def get_settings(db=Depends(database)):
        return s.settings(db)

    @app.put(api + '/settings', dependencies=access)
    def update_settings(data: m.Settings, db=Depends(database)):
        db.execute('UPDATE settings SET portions=? WHERE id=1', (data.portions,))
        db.executemany('UPDATE presence SET status=? WHERE day=? AND slot=?', [(p.status, p.day, p.slot) for p in data.presence])
        return s.settings(db)

    @app.post(api + '/weeks', dependencies=access)
    def create_week(data: m.Week, db=Depends(database)):
        return s.create_week(db, data.start)

    @app.get(api + '/weeks/{start}', dependencies=access)
    def get_week(start: date, db=Depends(database)):
        return s.week(db, start.isoformat())

    @app.post(api + '/weeks/{start}/template', dependencies=access)
    def apply_template(start: date, db=Depends(database)):
        current = s.week(db, start.isoformat())
        if any(meal['prepared'] or meal['title'] or meal['recipe_id'] or meal['side_id'] for meal in current['meals']):
            raise HTTPException(409, 'Le modèle ne peut être appliqué qu’à une semaine sans repas planifié.')
        model = s.settings(db)
        for entry in model['presence']:
            day = (start + timedelta(days=entry['day'])).isoformat()
            db.execute('UPDATE meals SET status=?,portions=? WHERE week_start=? AND day=? AND slot=?',
                       (entry['status'], model['portions'], start.isoformat(), day, entry['slot']))
        return s.week(db, start.isoformat())

    @app.get(api + '/weeks/{start}/needs', dependencies=access)
    def get_needs(start: date, db=Depends(database)):
        return s.needs(db, start.isoformat())

    @app.get(api + '/weeks/{start}/shopping', dependencies=access)
    def get_shopping(start: date, db=Depends(database)):
        return s.shopping(db, start.isoformat())

    @app.get(api + '/dashboard', dependencies=access)
    def dashboard(start: date, db=Depends(database)):
        return {'week': s.week(db, start.isoformat()), 'settings': s.settings(db), 'recipes': s.recipes(db),
                'ingredients': s.rows(db, 'SELECT * FROM ingredients ORDER BY name COLLATE NOCASE'),
                'stock': s.stock(db), 'shopping': s.shopping(db, start.isoformat()),
                'movements': [s.display(r) for r in s.rows(db, '''SELECT m.*,i.name,i.dimension FROM movements m
                   JOIN ingredients i ON i.id=m.ingredient_id ORDER BY m.id DESC LIMIT 100''')]}

    @app.put(api + '/meals/{ident}', dependencies=access)
    def update_meal(ident: int, data: m.Meal, db=Depends(database)):
        current = s.require(db, 'meals', ident)
        if current['prepared']:
            raise HTTPException(409, 'Ce repas est déjà préparé. Corriger le stock depuis son journal si nécessaire.')
        for recipe_id in (data.recipe_id, data.side_id):
            if recipe_id:
                s.require(db, 'recipes', recipe_id)
        db.execute('UPDATE meals SET status=?,title=?,recipe_id=?,side_id=?,portions=? WHERE id=?',
                   (data.status, data.title, data.recipe_id, data.side_id, data.portions, ident))
        return s.require(db, 'meals', ident)

    @app.post(api + '/meals/{ident}/prepare', dependencies=access)
    def prepare(ident: int, data: m.Preparation, db=Depends(database)):
        return s.prepare(db, ident, data)

    @app.post(api + '/ingredients', dependencies=access)
    def ingredient(data: m.Ingredient, db=Depends(database)):
        ident = db.execute('INSERT INTO ingredients (name,dimension) VALUES (?,?)', (data.name, data.dimension)).lastrowid
        return s.require(db, 'ingredients', ident)

    @app.put(api + '/ingredients/{ident}', dependencies=access)
    def update_ingredient(ident: int, data: m.Ingredient, db=Depends(database)):
        current = s.require(db, 'ingredients', ident)
        if current['dimension'] != data.dimension:
            used = db.execute('''SELECT 1 FROM recipe_ingredients WHERE ingredient_id=? UNION ALL
              SELECT 1 FROM stock WHERE ingredient_id=? UNION ALL SELECT 1 FROM shopping_manual WHERE ingredient_id=?''', (ident, ident, ident)).fetchone()
            if used:
                raise HTTPException(409, 'Un ingrédient utilisé conserve son type d’unité. Créer un ingrédient distinct.')
        db.execute('UPDATE ingredients SET name=?,dimension=? WHERE id=?', (data.name, data.dimension, ident))
        return s.require(db, 'ingredients', ident)

    @app.delete(api + '/ingredients/{ident}', dependencies=access)
    def delete_ingredient(ident: int, db=Depends(database)):
        s.require(db, 'ingredients', ident)
        db.execute('DELETE FROM ingredients WHERE id=?', (ident,))
        return {'ok': True}

    @app.post(api + '/recipes', dependencies=access)
    def recipe(data: m.Recipe, db=Depends(database)):
        return s.save_recipe(db, data)

    @app.post(api + '/recipes/import/preview', dependencies=[Depends(preview_access)])
    def import_preview(data: m.ImportPreview):
        from .recipe_import import preview
        from .safe_fetch import ImportProblem
        try:
            return preview(data.mode, data.url, data.text)
        except ImportProblem as error:
            raise HTTPException(422, str(error)) from None

    @app.post(api + '/recipes/import/photo/preview', dependencies=[Depends(preview_access)])
    def import_photo_preview(data: m.PhotoSource):
        import base64
        from . import photos
        from .safe_fetch import fetch_image, ImportProblem
        try:
            raw, source = fetch_image(data.url)
            image = photos.normalize(raw)
            return {'data_base64': base64.b64encode(image['data']).decode('ascii'),
                    'width': image['width'], 'height': image['height'],
                    'source_url': source, 'attribution': data.attribution}
        except ImportProblem as error:
            raise HTTPException(422, str(error)) from None

    @app.put(api + '/recipes/{ident}/photo', dependencies=[Depends(preview_access)])
    async def upload_recipe_photo(ident: int, request: Request):
        from . import photos
        with connect(path) as db:
            s.require(db, 'recipes', ident)
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > photos.MAX_UPLOAD:
                raise HTTPException(413, 'Choisir une photo de 12 Mio maximum.')
            raw.extend(chunk)
        image = await run_in_threadpool(photos.normalize, bytes(raw))
        with connect(path) as db:
            return photos.save(db, ident, image)

    @app.put(api + '/recipes/{ident}/photo/confirm', dependencies=access)
    def confirm_recipe_photo(ident: int, data: m.PhotoDraft, db=Depends(database)):
        from . import photos
        return photos.save(db, ident, photos.from_draft(data), data.source_url, data.attribution)

    @app.get(api + '/recipes/{ident}/photo', dependencies=access)
    def get_recipe_photo(ident: int, db=Depends(database)):
        s.require(db, 'recipes', ident)
        photo = db.execute('SELECT data FROM recipe_photos WHERE recipe_id=?', (ident,)).fetchone()
        if photo is None:
            raise HTTPException(404, 'Cette recette n’a pas de photo.')
        return Response(bytes(photo['data']), media_type='image/jpeg')

    @app.delete(api + '/recipes/{ident}/photo', dependencies=access)
    def delete_recipe_photo(ident: int, db=Depends(database)):
        s.require(db, 'recipes', ident)
        db.execute('DELETE FROM recipe_photos WHERE recipe_id=?', (ident,))
        return {'ok': True}

    @app.post(api + '/recipes/import/confirm', dependencies=access)
    def import_confirmation(data: m.ImportConfirmation, db=Depends(database)):
        return s.confirm_import(db, data)

    @app.patch(api + '/recipes/{ident}/preferences', dependencies=access)
    def recipe_preferences(ident: int, data: m.RecipePreferences, db=Depends(database)):
        from .comfort import preferences
        return preferences(db, ident, data)

    @app.get(api + '/history', dependencies=access)
    def prepared_history(limit: int = Query(50, ge=1, le=100), before: int | None = Query(None, gt=0), db=Depends(database)):
        from .comfort import history
        values = history(db, limit, before)
        return {'items': values, 'next_before': values[-1]['meal_id'] if len(values) == limit else None}

    @app.get(api + '/suggestions/web/sources', dependencies=access)
    def web_sources(db=Depends(database)):
        from .web_ideas import SOURCE, INDEX_URL
        return {'items': [{'id': 0, 'name': SOURCE, 'url': INDEX_URL},
                          *[dict(row) for row in db.execute('SELECT * FROM web_sources ORDER BY id')]]}

    @app.post(api + '/suggestions/web/sources', dependencies=[Depends(preview_access)])
    def add_web_source(data: m.WebSource):
        from . import web_ideas as web
        from .safe_fetch import ImportProblem
        from urllib.parse import urlsplit
        url = web.normalized_link(data.url)
        if not url:
            raise HTTPException(422, 'Utiliser un lien HTTP ou HTTPS public sans identifiants.')

        def check(db):
            if db.execute('SELECT 1 FROM web_sources WHERE url=?', (url,)).fetchone():
                raise HTTPException(409, 'Ce lien est déjà dans vos sources.')
            if db.execute('SELECT COUNT(*) FROM web_sources').fetchone()[0] >= web.MAX_SOURCES:
                raise HTTPException(409, 'Vous pouvez conserver 20 liens. Retirez une source avant d’en ajouter une autre.')

        with connect(path) as db:
            check(db)
        try:
            items = web.source_catalogue(url)
        except ImportProblem as error:
            raise HTTPException(422, 'Lien non ajouté. ' + str(error)) from None
        with connect(path) as db:
            check(db)
            name = urlsplit(url).hostname
            ident = db.execute('INSERT INTO web_sources (name,url) VALUES (?,?)', (name, url)).lastrowid
        return {'id': ident, 'name': name, 'url': url, 'count': len(items)}

    @app.delete(api + '/suggestions/web/sources/{ident}', dependencies=access)
    def delete_web_source(ident: int, db=Depends(database)):
        if not db.execute('SELECT 1 FROM web_sources WHERE id=?', (ident,)).fetchone():
            raise HTTPException(404, 'Source introuvable. La source initiale est conservée.')
        db.execute('DELETE FROM web_sources WHERE id=?', (ident,))
        return {'ok': True}

    @app.post(api + '/suggestions/web', dependencies=[Depends(preview_access)])
    def web_suggestion(data: m.WebDiscovery):
        from .web_ideas import discover
        from .safe_fetch import ImportProblem
        # Release SQLite before requesting the public index.
        with connect(path) as db:
            saved = [row['source_url'] for row in db.execute("SELECT source_url FROM recipes WHERE source_url != ''")]
            source = None
            if data.source_id:
                source = db.execute('SELECT url FROM web_sources WHERE id=?', (data.source_id,)).fetchone()
                if not source:
                    raise HTTPException(404, 'Cette source a été retirée. Choisissez une autre source.')
        try:
            return discover(data.exclude, saved, source['url'] if source else None)
        except ImportProblem as error:
            raise HTTPException(422, 'Découverte web indisponible. ' + str(error)) from None

    @app.get(api + '/suggestions', dependencies=access)
    def recipe_suggestions(day: date, mode: str = 'varier', portions: int = Query(4, ge=1, le=30), exclude: str = Query('', max_length=2000), db=Depends(database)):
        from .comfort import suggestions
        try:
            excluded = {int(value) for value in exclude.split(',') if value}
        except ValueError:
            raise HTTPException(422, 'Liste d’exclusion invalide.') from None
        return {'items': suggestions(db, mode, day, portions, excluded)}

    @app.get(api + '/weeks/{start}/copy-preview', dependencies=access)
    def week_copy_preview(start: date, source_start: date, db=Depends(database)):
        from .comfort import copy_preview
        return copy_preview(db, start.isoformat(), source_start.isoformat())

    @app.post(api + '/weeks/{start}/copy', dependencies=access)
    def week_copy(start: date, data: m.CopyWeek, db=Depends(database)):
        from .comfort import copy_week
        return copy_week(db, start.isoformat(), data)

    @app.post(api + '/meals/{ident}/reuse', dependencies=access)
    def meal_reuse(ident: int, data: m.ReuseMeal, db=Depends(database)):
        from .comfort import reuse
        def perform():
            reuse(db, ident, data.source_meal_id)
            return {'reused': ident}
        return s.operation(db, data, f'reuse:{ident}', perform)

    @app.post(api + '/meals/{ident}/suggestion', dependencies=access)
    def plan_suggestion(ident: int, data: m.PlanSuggestion, db=Depends(database)):
        from .comfort import empty_home
        def perform():
            if not empty_home(s.require(db, 'meals', ident)):
                raise HTTPException(409, 'Le créneau a changé : choisir un repas maison vide.')
            s.require(db, 'recipes', data.recipe_id)
            db.execute('UPDATE meals SET recipe_id=? WHERE id=?', (data.recipe_id, ident))
            return {'planned': ident}
        return s.operation(db, data, f'suggestion:{ident}', perform)

    @app.get(api + '/weeks/{start}/shopping/offline', dependencies=access)
    def shopping_offline(start: date, db=Depends(database)):
        from .offline_shopping import snapshot
        return snapshot(db, start.isoformat())

    @app.post(api + '/shopping/sync', dependencies=access)
    def shopping_sync(data: m.OfflineSync, db=Depends(database)):
        from .offline_shopping import sync
        return sync(db, data)

    @app.put(api + '/recipes/{ident}', dependencies=access)
    def update_recipe(ident: int, data: m.Recipe, db=Depends(database)):
        return s.save_recipe(db, data, ident)

    @app.delete(api + '/recipes/{ident}', dependencies=access)
    def delete_recipe(ident: int, db=Depends(database)):
        s.require(db, 'recipes', ident)
        db.execute('DELETE FROM recipes WHERE id=?', (ident,))
        return {'ok': True}

    @app.post(api + '/stock', dependencies=access)
    def stock(data: m.Stock, db=Depends(database)):
        return s.add_stock(db, data)

    @app.patch(api + '/stock/{ident}', dependencies=access)
    def correct_stock(ident: int, data: m.Correction, db=Depends(database)):
        lot = s.require(db, 'stock', ident)
        q = s.quantity(db, lot['ingredient_id'], data.quantity, data.unit)
        db.execute('UPDATE stock SET quantity=? WHERE id=?', (q, ident))
        s.movement(db, lot['ingredient_id'], ident, q - lot['quantity'], data.reason)
        return {'ok': True}

    @app.post(api + '/weeks/{start}/shopping/manual', dependencies=access)
    def add_manual(start: date, data: m.Manual, db=Depends(database)):
        s.week(db, start.isoformat())
        q = s.quantity(db, data.ingredient_id, data.quantity, data.unit)
        ident = db.execute('INSERT INTO shopping_manual (week_start,ingredient_id,quantity) VALUES (?,?,?)', (start.isoformat(), data.ingredient_id, q)).lastrowid
        return {'id': ident}

    @app.delete(api + '/weeks/{start}/shopping/manual/{ident}', dependencies=access)
    def delete_manual(start: date, ident: int, db=Depends(database)):
        row = s.require(db, 'shopping_manual', ident)
        if row['week_start'] != start.isoformat() or row['purchased']:
            raise HTTPException(409, 'Cet article ne peut plus être retiré de cette liste.')
        db.execute('DELETE FROM shopping_manual WHERE id=?', (ident,))
        return {'ok': True}

    @app.patch(api + '/weeks/{start}/shopping/check', dependencies=access)
    def check(start: date, data: m.Check, db=Depends(database)):
        key = start.isoformat()
        current = s.shopping(db, key)['items']
        if data.manual_id:
            if not any(i['manual_id'] == data.manual_id for i in current):
                raise HTTPException(404, 'Article introuvable dans cette liste.')
            db.execute('UPDATE shopping_manual SET checked=? WHERE id=?', (data.checked, data.manual_id))
        else:
            if not any(i['manual_id'] is None and i['ingredient_id'] == data.ingredient_id for i in current):
                raise HTTPException(409, 'Les besoins de cet article ont changé.')
            db.execute('INSERT INTO shopping_checks VALUES (?,?,?) ON CONFLICT(week_start,ingredient_id) DO UPDATE SET checked=excluded.checked', (key, data.ingredient_id, data.checked))
        return {'ok': True}

    @app.post(api + '/weeks/{start}/shopping/complete', dependencies=access)
    def complete(start: date, data: m.Purchase, db=Depends(database)):
        return s.purchase(db, start.isoformat(), data)

    static = Path(os.getenv('MIJOTE_STATIC_DIR', str(Path(__file__).resolve().parents[2] / 'frontend/dist')))

    @app.post('/share-recipe')
    async def receive_recipe_share(request: Request):
        from .recipe_share import receive
        return await receive(request, static)

    if static.is_dir():
        app.mount('/assets', StaticFiles(directory=static / 'assets'), name='assets')

        @app.get('/{filename:path}')
        def frontend(filename: str):
            if filename.startswith('api/'):
                raise HTTPException(404, 'Route inconnue.')
            target = (static / filename).resolve()
            if target.is_relative_to(static.resolve()) and target.is_file():
                return FileResponse(target)
            return FileResponse(static / 'index.html')

    return app


app = create_app()
