from alembic import context
from flask import current_app

config = context.config
db = current_app.extensions['migrate'].db
target_metadata = db.metadata


def run_migrations():
    if context.is_offline_mode():
        raise RuntimeError('Esta migración requiere conexión para conservar las tablas existentes.')
    with db.engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


run_migrations()
