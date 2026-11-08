"""Private source links for web discoveries."""
from alembic import op

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''CREATE TABLE web_sources (
      id INTEGER PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL UNIQUE)''')


def downgrade():
    raise RuntimeError('Restore an explicit backup instead of removing saved source links.')
