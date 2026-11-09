"""Additional meal dishes and direct ingredients, preserving legacy main/side fields."""
from alembic import op

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''CREATE TABLE meal_dishes (
      meal_id INTEGER NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
      role TEXT NOT NULL CHECK(role IN ('dish','side')), position INTEGER NOT NULL,
      recipe_id INTEGER REFERENCES recipes(id), ingredient_id INTEGER REFERENCES ingredients(id),
      title TEXT NOT NULL DEFAULT '', quantity INTEGER,
      course TEXT NOT NULL DEFAULT 'plat' CHECK(course IN ('entree','plat','dessert')),
      PRIMARY KEY(meal_id,role,position),
      CHECK((recipe_id IS NOT NULL)+(ingredient_id IS NOT NULL)+(title!='')=1),
      CHECK((ingredient_id IS NULL AND quantity IS NULL) OR (ingredient_id IS NOT NULL AND quantity>0)),
      CHECK(role!='side' OR (ingredient_id IS NOT NULL AND position=0)))''')
    op.execute('''CREATE TABLE meal_history_dishes (
      meal_id INTEGER NOT NULL REFERENCES meal_history(meal_id) ON DELETE CASCADE,
      position INTEGER NOT NULL, recipe_id INTEGER REFERENCES recipes(id), name TEXT NOT NULL,
      course TEXT NOT NULL DEFAULT 'plat' CHECK(course IN ('entree','plat','dessert')),
      PRIMARY KEY(meal_id,position))''')


def downgrade():
    raise RuntimeError('Restore an explicit backup instead of removing meal dishes.')
