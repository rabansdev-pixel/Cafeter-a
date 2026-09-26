"""Persist product images in PostgreSQL, including on ephemeral deployments."""
from alembic import op
import sqlalchemy as sa

revision = '20260925_product_images'
down_revision = '20260925_store_accounts'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('product_images',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('data', sa.LargeBinary, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))


def downgrade():
    raise RuntimeError('No se borran fotos automáticamente: prepara una reversión con respaldo.')
