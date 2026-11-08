"""Phase A foundations.

Revision ID: 0001
"""
from alembic import op
from app.schema import SCHEMA

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    for statement in SCHEMA:
        op.execute(statement)


def downgrade():
    raise RuntimeError('Destructive downgrade disabled; restore an explicit backup instead.')
