"""Link existing users to Firebase without replacing roles or local identities."""
from alembic import op
import sqlalchemy as sa

revision = '20260925_firebase_auth'
down_revision = '20260925_spanish_tables'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('usuarios', sa.Column('firebase_uid', sa.String(128)))
    op.create_unique_constraint('uq_usuarios_firebase_uid', 'usuarios', ['firebase_uid'])
    op.alter_column('usuarios', 'password_hash', existing_type=sa.String(255), nullable=True)
    op.create_table('sesiones_firebase',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('usuarios.id'), nullable=False),
        sa.Column('user_version', sa.Integer, nullable=False),
        sa.Column('encrypted_tokens', sa.Text, nullable=False),
        sa.Column('authenticated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_sesiones_firebase_user_id', 'sesiones_firebase', ['user_id'])
    op.create_index('ix_sesiones_firebase_expires_at', 'sesiones_firebase', ['expires_at'])


def downgrade():
    raise RuntimeError('No se puede restaurar una contraseña local desde Firebase. Prepara una reversión explícita.')
