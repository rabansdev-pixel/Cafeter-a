"""Limited coupon campaigns and immutable redemption receipts."""
from alembic import op
import sqlalchemy as sa
revision = '20260927_coupons'
down_revision = '20260925_firebase_auth'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('cupones', sa.Column('id', sa.Integer, primary_key=True), sa.Column('code', sa.String(40), nullable=False, unique=True), sa.Column('kind', sa.String(16), nullable=False), sa.Column('percent', sa.Integer, nullable=False), sa.Column('take', sa.Integer, nullable=False), sa.Column('pay', sa.Integer, nullable=False), sa.Column('capacity', sa.Integer, nullable=False), sa.Column('used', sa.Integer, nullable=False), sa.Column('active', sa.Boolean, nullable=False), sa.Column('expires', sa.DateTime(timezone=True)), sa.CheckConstraint('capacity > 0 AND used >= 0 AND used <= capacity', name='coupon_capacity'), sa.CheckConstraint("(kind = 'percent' AND percent BETWEEN 1 AND 100) OR (kind = 'bundle' AND take BETWEEN 2 AND 99 AND pay >= 1 AND pay < take)", name='coupon_discount'))
    op.create_table('canjes_cupon', sa.Column('id', sa.String(36), primary_key=True), sa.Column('coupon_id', sa.Integer, sa.ForeignKey('cupones.id'), nullable=False), sa.Column('user_id', sa.Integer, sa.ForeignKey('usuarios.id'), nullable=False), sa.Column('snapshot', sa.JSON, nullable=False), sa.Column('cancelled', sa.Boolean, nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint('coupon_id', 'user_id', name='one_coupon_per_user'))

def downgrade():
    op.drop_table('canjes_cupon')
    op.drop_table('cupones')
