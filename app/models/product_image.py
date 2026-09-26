"""Immutable uploaded product photos, persisted with the product transaction."""
from uuid import uuid4
from app.core.extensions import db
from app.models.identity import now


class ProductImage(db.Model):
    __tablename__ = 'imagenes_productos'
    id = db.Column(db.String(32), primary_key=True, default=lambda: uuid4().hex)
    data = db.deferred(db.Column(db.LargeBinary, nullable=False))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
