"""Recipe preferences, confirmed-meal history and versioned offline shopping.

Revision ID: 0003
"""
from uuid import uuid4
from alembic import op

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    for statement in [
        "ALTER TABLE recipes ADD COLUMN favorite INTEGER NOT NULL DEFAULT 0 CHECK(favorite IN (0,1))",
        "ALTER TABLE recipes ADD COLUMN to_try INTEGER NOT NULL DEFAULT 0 CHECK(to_try IN (0,1))",
        "ALTER TABLE recipes ADD COLUMN rating TEXT NOT NULL DEFAULT '' CHECK(rating IN ('','a_refaire','pas_mal','a_ameliorer','ne_plus_proposer'))",
        "ALTER TABLE recipes ADD COLUMN category TEXT NOT NULL DEFAULT 'autre' CHECK(category IN ('autre','viande','poisson','legumes','vegetarien','feculents','dessert'))",
        "ALTER TABLE recipes ADD COLUMN comment TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE recipes ADD COLUMN variant TEXT NOT NULL DEFAULT ''",
        """CREATE TABLE meal_history (meal_id INTEGER PRIMARY KEY REFERENCES meals(id),
           planned_day TEXT NOT NULL, slot TEXT NOT NULL, prepared_at TEXT,
           main_recipe_id INTEGER REFERENCES recipes(id), side_recipe_id INTEGER REFERENCES recipes(id),
           main_name TEXT NOT NULL, side_name TEXT NOT NULL, portions INTEGER NOT NULL)""",
        """INSERT INTO meal_history SELECT m.id,m.day,m.slot,NULL,m.recipe_id,m.side_id,
           COALESCE(r.name,NULLIF(m.title,''),'Repas sans intitulé'),COALESCE(s.name,''),m.portions
           FROM meals m LEFT JOIN recipes r ON r.id=m.recipe_id LEFT JOIN recipes s ON s.id=m.side_id
           WHERE m.prepared=1""",
        "CREATE INDEX history_date ON meal_history(prepared_at,planned_day)",
        "CREATE TABLE app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
        """CREATE TABLE shopping_revisions (week_start TEXT NOT NULL, item_key TEXT NOT NULL,
           revision INTEGER NOT NULL, PRIMARY KEY(week_start,item_key))""",
    ]:
        op.execute(statement)
    op.execute(f"INSERT INTO app_meta VALUES ('household_id','{uuid4()}')")
    # Revision counters survive deletion/recreation of a manual row and catch ABA changes.
    for table, actions, key in [
        ('shopping_checks', ('INSERT', 'UPDATE'), "'auto-' || NEW.ingredient_id"),
        ('shopping_manual', ('INSERT', 'UPDATE', 'DELETE'), "'manual-' || NEW.id"),
    ]:
        for action in actions:
            row = 'OLD' if action == 'DELETE' else 'NEW'
            item_key = key.replace('NEW.', row + '.')
            op.execute(f"""CREATE TRIGGER {table}_{action.lower()}_revision AFTER {action} ON {table}
              BEGIN INSERT INTO shopping_revisions VALUES ({row}.week_start,{item_key},1)
              ON CONFLICT(week_start,item_key) DO UPDATE SET revision=revision+1; END""")


def downgrade():
    raise RuntimeError('Restore an explicit backup instead of removing household history.')
