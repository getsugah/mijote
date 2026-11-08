"""Keep attribution and original unquantified ingredient text.

Revision ID: 0002
"""
from alembic import op

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE recipes ADD COLUMN source_author TEXT NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE recipes ADD COLUMN ingredient_notes TEXT NOT NULL DEFAULT ''")


def downgrade():
    raise RuntimeError('Restore a backup instead of removing recipe attribution.')
