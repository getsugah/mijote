"""Optional recipe tags; no modification to existing recipes or photos."""
from alembic import op

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE TABLE tags(id INTEGER PRIMARY KEY, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE)')
    op.execute('CREATE TABLE recipe_tags(recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE, tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE, PRIMARY KEY(recipe_id,tag_id))')
    op.execute('CREATE INDEX recipe_tags_by_tag ON recipe_tags(tag_id,recipe_id)')


def downgrade():
    raise RuntimeError('Restaurer une sauvegarde explicite pour revenir avant les tags.')
