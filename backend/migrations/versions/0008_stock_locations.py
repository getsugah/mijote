"""Editable stock labels and persistent locations; preserve lots and movements."""
import unicodedata
from alembic import op
import sqlalchemy as sa

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE stock ADD COLUMN label TEXT NOT NULL DEFAULT ''")
    op.execute('CREATE TABLE stock_locations(id INTEGER PRIMARY KEY, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE)')
    connection = op.get_bind()
    existing = [row[0] for row in connection.execute(sa.text('SELECT DISTINCT location FROM stock ORDER BY id'))]
    for original in ['Placard', 'Réfrigérateur', 'Congélateur', *existing]:
        name = ' '.join(original.split())
        if not name:
            name = 'Placard'
        key = unicodedata.normalize('NFKC', name).casefold()
        connection.execute(sa.text('INSERT OR IGNORE INTO stock_locations(name,name_key) VALUES (:name,:key)'), {'name': name, 'key': key})
        canonical = connection.execute(sa.text('SELECT name FROM stock_locations WHERE name_key=:key'), {'key': key}).scalar_one()
        connection.execute(sa.text('UPDATE stock SET location=:name WHERE location=:original'), {'name': canonical, 'original': original})


def downgrade():
    raise RuntimeError('Restaurer une sauvegarde explicite pour revenir avant les emplacements.')
