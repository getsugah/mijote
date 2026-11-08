from alembic import context
from sqlalchemy import create_engine, pool

engine = create_engine(context.config.get_main_option('sqlalchemy.url'), poolclass=pool.NullPool)
with engine.connect() as connection:
    context.configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()
