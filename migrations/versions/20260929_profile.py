from alembic import op
import sqlalchemy as sa
revision = '20260929_profile'
down_revision = '20260928_inquiries'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('usuarios', sa.Column('whatsapp', sa.String(20), nullable=False, server_default=''))
    op.add_column('usuarios', sa.Column('profile_completed', sa.Boolean, nullable=False, server_default=sa.true()))
    op.alter_column('usuarios', 'profile_completed', server_default=sa.false())

def downgrade():
    op.drop_column('usuarios', 'profile_completed')
    op.drop_column('usuarios', 'whatsapp')
