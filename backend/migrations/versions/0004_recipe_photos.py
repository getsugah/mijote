"""Private normalized recipe images, included in existing SQLite backups."""
from alembic import op

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''CREATE TABLE recipe_photos (
      recipe_id INTEGER PRIMARY KEY REFERENCES recipes(id) ON DELETE CASCADE,
      data BLOB NOT NULL CHECK(length(data) BETWEEN 1 AND 524288),
      digest TEXT NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL,
      source_url TEXT NOT NULL DEFAULT '', attribution TEXT NOT NULL DEFAULT '',
      updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')))''')


def downgrade():
    raise RuntimeError('Restore an explicit backup instead of removing household photos.')
