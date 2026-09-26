"""Adopt the existing legacy schema and add store accounts without deleting data."""
from alembic import op
import sqlalchemy as sa

revision = '20260925_store_accounts'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    # Serializes simultaneous deploy migrations against the same database.
    connection.execute(sa.text('SELECT pg_advisory_xact_lock(2409202600)'))
    tables = set(sa.inspect(connection).get_table_names())
    if 'origins' not in tables:
        op.create_table('origins', sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('country', sa.String(80), nullable=False), sa.Column('region', sa.String(100), nullable=False),
            sa.Column('farm', sa.String(120)), sa.Column('altitude_meters', sa.Integer, nullable=False),
            sa.Column('process', sa.String(60), nullable=False), sa.Column('variety', sa.String(80)))
    if 'tasting_profiles' not in tables:
        op.create_table('tasting_profiles', sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('roast_level', sa.String(40), nullable=False),
            sa.Column('acidity', sa.Integer, nullable=False), sa.Column('body', sa.Integer, nullable=False),
            sa.Column('sweetness', sa.Integer, nullable=False), sa.Column('aroma', sa.Integer, nullable=False),
            sa.Column('flavor_notes', sa.String(255), nullable=False))
    if 'products' not in tables:
        op.create_table('products', sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('name', sa.String(120), nullable=False), sa.Column('slug', sa.String(140), nullable=False),
            sa.Column('tagline', sa.String(200), nullable=False), sa.Column('description', sa.Text, nullable=False),
            sa.Column('price', sa.Numeric(12, 2), nullable=False), sa.Column('stock', sa.Integer),
            sa.Column('weight_grams', sa.Integer, nullable=False), sa.Column('image_url', sa.String(255), nullable=False),
            sa.Column('is_featured', sa.Boolean), sa.Column('is_active', sa.Boolean), sa.Column('created_at', sa.DateTime),
            sa.Column('origin_id', sa.Integer, sa.ForeignKey('origins.id')),
            sa.Column('tasting_profile_id', sa.Integer, sa.ForeignKey('tasting_profiles.id')))
        op.create_index('ix_products_slug', 'products', ['slug'], unique=True)
        op.create_index('ix_products_is_featured', 'products', ['is_featured'])
    else:
        op.alter_column('products', 'price', type_=sa.Numeric(12, 2), postgresql_using='round(price::numeric, 2)')
        for column in ('stock', 'origin_id', 'tasting_profile_id'):
            op.alter_column('products', column, nullable=True)
    op.create_table('categories', sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(120), nullable=False, unique=True),
        sa.Column('intro', sa.Text, nullable=False), sa.Column('position', sa.Integer, nullable=False))
    op.add_column('products', sa.Column('category_id', sa.Integer, sa.ForeignKey('categories.id')))
    op.create_index('ix_products_category_id', 'products', ['category_id'])
    op.add_column('products', sa.Column('menu_id', sa.String(160)))
    op.create_unique_constraint('uq_products_menu_id', 'products', ['menu_id'])
    op.add_column('products', sa.Column('position', sa.Integer, nullable=False, server_default='0'))
    op.add_column('products', sa.Column('details', sa.JSON, nullable=False, server_default=sa.text("'{}'::json")))
    op.add_column('products', sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()))
    op.execute('UPDATE products SET updated_at = COALESCE(created_at, CURRENT_TIMESTAMP)')
    for column in ('position', 'details', 'updated_at'):
        op.alter_column('products', column, server_default=None)
    op.create_check_constraint('products_price_nonnegative', 'products', 'price >= 0')
    op.create_check_constraint('products_stock_nonnegative', 'products', 'stock IS NULL OR stock >= 0')
    op.create_table('users', sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(120), nullable=False), sa.Column('email', sa.String(254), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False), sa.Column('role', sa.String(20), nullable=False),
        sa.Column('active', sa.Boolean, nullable=False), sa.Column('session_version', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('customer', 'staff', 'admin')", name='users_role_valid'))
    op.create_table('audit_logs', sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('actor_id', sa.Integer, sa.ForeignKey('users.id')), sa.Column('action', sa.String(60), nullable=False),
        sa.Column('entity', sa.String(40), nullable=False), sa.Column('entity_id', sa.Integer),
        sa.Column('changes', sa.JSON, nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('access_attempts', sa.Column('key', sa.String(64), primary_key=True),
        sa.Column('attempts', sa.Integer, nullable=False), sa.Column('started_at', sa.DateTime(timezone=True), nullable=False))


def downgrade():
    raise RuntimeError('Reversión destructiva bloqueada: conserva un respaldo y prepara una migración explícita.')
