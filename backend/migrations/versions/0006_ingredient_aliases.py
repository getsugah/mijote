"""Confirmed ingredient aliases and redirects; existing ingredients remain intact."""
from alembic import op

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''CREATE TABLE ingredient_aliases (
      name TEXT PRIMARY KEY, display_name TEXT NOT NULL,
      ingredient_id INTEGER NOT NULL REFERENCES ingredients(id))''')
    op.execute('''CREATE TABLE ingredient_redirects (
      source_id INTEGER PRIMARY KEY REFERENCES ingredients(id),
      target_id INTEGER NOT NULL REFERENCES ingredients(id), CHECK(source_id != target_id))''')


def downgrade():
    raise RuntimeError('Restore an explicit backup instead of removing confirmed ingredient links.')
