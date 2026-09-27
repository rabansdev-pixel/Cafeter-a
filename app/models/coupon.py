from app.core.extensions import db
from app.models.identity import now


class Coupon(db.Model):
    __tablename__ = 'cupones'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    kind = db.Column(db.String(16), nullable=False)
    percent = db.Column(db.Integer, nullable=False, default=0)
    take = db.Column(db.Integer, nullable=False, default=3)
    pay = db.Column(db.Integer, nullable=False, default=2)
    capacity = db.Column(db.Integer, nullable=False)
    used = db.Column(db.Integer, nullable=False, default=0)
    active = db.Column(db.Boolean, nullable=False, default=True)
    expires = db.Column(db.DateTime(timezone=True))
    __table_args__ = (db.CheckConstraint('capacity > 0 AND used >= 0 AND used <= capacity', name='coupon_capacity'), db.CheckConstraint("(kind = 'percent' AND percent BETWEEN 1 AND 100) OR (kind = 'bundle' AND take BETWEEN 2 AND 99 AND pay >= 1 AND pay < take)", name='coupon_discount'))


class CouponRedemption(db.Model):
    __tablename__ = 'canjes_cupon'
    id = db.Column(db.String(36), primary_key=True)
    coupon_id = db.Column(db.Integer, db.ForeignKey('cupones.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    snapshot = db.Column(db.JSON, nullable=False)
    cancelled = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
    __table_args__ = (db.UniqueConstraint('coupon_id', 'user_id', name='one_coupon_per_user'),)
