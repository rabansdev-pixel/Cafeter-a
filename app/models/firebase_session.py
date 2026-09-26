"""Server-side Firebase sessions: tokens never enter the Flask session cookie."""
from uuid import uuid4
from app.core.extensions import db
from app.models.identity import now


class FirebaseSession(db.Model):
    __tablename__ = 'sesiones_firebase'
    id = db.Column(db.String(32), primary_key=True, default=lambda: uuid4().hex)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    user_version = db.Column(db.Integer, nullable=False)
    encrypted_tokens = db.Column(db.Text, nullable=False)
    authenticated_at = db.Column(db.DateTime(timezone=True), nullable=False)
    token_expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    checked_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
