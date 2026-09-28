from alembic import op
import sqlalchemy as sa
revision = '20260928_inquiries'
down_revision = '20260927_coupons'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('consultas', sa.Column('reference', sa.String(24), primary_key=True), sa.Column('user_id', sa.Integer, sa.ForeignKey('usuarios.id')), sa.Column('customer', sa.String(120), nullable=False), sa.Column('snapshot', sa.JSON, nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))

def downgrade():
    op.drop_table('consultas')
