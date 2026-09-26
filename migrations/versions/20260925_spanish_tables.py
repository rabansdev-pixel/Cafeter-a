"""Rename business tables to Spanish without recreating or copying records."""
from alembic import op

revision = '20260925_spanish_tables'
down_revision = '20260925_product_images'
branch_labels = None
depends_on = None

TABLES = (
    ('origins', 'origenes'),
    ('tasting_profiles', 'perfiles_cata'),
    ('categories', 'categorias'),
    ('products', 'productos'),
    ('users', 'usuarios'),
    ('audit_logs', 'registro_actividad'),
    ('access_attempts', 'intentos_acceso'),
    ('product_images', 'imagenes_productos'),
)
INDEXES = (
    ('ix_products_slug', 'ix_productos_slug'),
    ('ix_products_is_featured', 'ix_productos_is_featured'),
    ('ix_products_category_id', 'ix_productos_category_id'),
)


def upgrade():
    # PostgreSQL preserves rows, IDs, sequences and FK references on RENAME.
    for old, new in TABLES:
        op.rename_table(old, new)
    for old, new in INDEXES:
        op.execute(f'ALTER INDEX "{old}" RENAME TO "{new}"')


def downgrade():
    for old, new in reversed(INDEXES):
        op.execute(f'ALTER INDEX "{new}" RENAME TO "{old}"')
    for old, new in reversed(TABLES):
        op.rename_table(new, old)
