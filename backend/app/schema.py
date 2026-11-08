"""Initial schema, owned by Alembic. All inventory quantities use integer milli-units."""

SCHEMA = [
    """CREATE TABLE users (id INTEGER PRIMARY KEY CHECK(id=1), name TEXT NOT NULL,
       password_hash TEXT NOT NULL)""",
    """CREATE TABLE sessions (token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
       csrf TEXT NOT NULL, expires INTEGER NOT NULL)""",
    """CREATE TABLE settings (id INTEGER PRIMARY KEY CHECK(id=1), portions INTEGER NOT NULL CHECK(portions BETWEEN 1 AND 30))""",
    "INSERT INTO settings VALUES (1,4)",
    """CREATE TABLE presence (day INTEGER NOT NULL CHECK(day BETWEEN 0 AND 6), slot TEXT NOT NULL
       CHECK(slot IN ('midi','soir')), status TEXT NOT NULL CHECK(status IN ('maison','travail','exterieur','a_decider')),
       PRIMARY KEY(day,slot))""",
    """CREATE TABLE ingredients (id INTEGER PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE,
       dimension TEXT NOT NULL CHECK(dimension IN ('masse','volume','piece')))""",
    """CREATE TABLE products (id INTEGER PRIMARY KEY, ingredient_id INTEGER REFERENCES ingredients(id),
       name TEXT NOT NULL, brand TEXT, barcode TEXT UNIQUE, package_quantity INTEGER, package_unit TEXT)""",
    """CREATE TABLE recipes (id INTEGER PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL
       CHECK(kind IN ('simple','improvise','recette')), portions INTEGER NOT NULL CHECK(portions BETWEEN 1 AND 30),
       steps TEXT NOT NULL DEFAULT '', minutes INTEGER NOT NULL DEFAULT 0, source_url TEXT NOT NULL DEFAULT '')""",
    """CREATE TABLE recipe_ingredients (recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
       ingredient_id INTEGER NOT NULL REFERENCES ingredients(id), quantity INTEGER NOT NULL CHECK(quantity>0),
       PRIMARY KEY(recipe_id,ingredient_id))""",
    """CREATE TABLE weeks (start TEXT PRIMARY KEY)""",
    """CREATE TABLE meals (id INTEGER PRIMARY KEY, week_start TEXT NOT NULL REFERENCES weeks(start),
       day TEXT NOT NULL, slot TEXT NOT NULL CHECK(slot IN ('midi','soir')), status TEXT NOT NULL
       CHECK(status IN ('maison','travail','exterieur','a_decider')), title TEXT NOT NULL DEFAULT '',
       recipe_id INTEGER REFERENCES recipes(id), side_id INTEGER REFERENCES recipes(id),
       portions INTEGER NOT NULL CHECK(portions BETWEEN 1 AND 30), prepared INTEGER NOT NULL DEFAULT 0,
       UNIQUE(day,slot))""",
    """CREATE TABLE stock (id INTEGER PRIMARY KEY, ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
       location TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>=0), expires TEXT)""",
    """CREATE TABLE movements (id INTEGER PRIMARY KEY, ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
       stock_id INTEGER REFERENCES stock(id), delta INTEGER NOT NULL, reason TEXT NOT NULL,
       created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')), operation_id TEXT)""",
    """CREATE TABLE shopping_manual (id INTEGER PRIMARY KEY, week_start TEXT NOT NULL REFERENCES weeks(start), ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
       quantity INTEGER NOT NULL CHECK(quantity>0), checked INTEGER NOT NULL DEFAULT 0, purchased INTEGER NOT NULL DEFAULT 0)""",
    """CREATE TABLE shopping_checks (week_start TEXT NOT NULL REFERENCES weeks(start), ingredient_id INTEGER NOT NULL
       REFERENCES ingredients(id), checked INTEGER NOT NULL, PRIMARY KEY(week_start,ingredient_id))""",
    """CREATE TABLE operations (id TEXT PRIMARY KEY, kind TEXT NOT NULL, request_hash TEXT NOT NULL, response TEXT NOT NULL)""",
    "CREATE INDEX stock_ingredient ON stock(ingredient_id)",
    "CREATE INDEX meals_week ON meals(week_start)",
    "CREATE INDEX movements_ingredient ON movements(ingredient_id)",
]
