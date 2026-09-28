from app.core.extensions import db
from app.models.identity import now

class Inquiry(db.Model):
    __tablename__ = 'consultas'
    reference = db.Column(db.String(24), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    customer = db.Column(db.String(120), nullable=False)
    snapshot = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
