import re
import secrets
from uuid import uuid4
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, g, render_template, flash, redirect, url_for, abort
from app.core.extensions import db
from app.models import Coupon, CouponRedemption
from app.services.auth_service import require_user
from app.services.menu_service import MenuService, money, MenuError

coupon_bp = Blueprint('coupons', __name__)


def offer(coupon, items):
    if not coupon.active:
        raise ValueError('Este cupón está desactivado.')
    if coupon.expires and coupon.expires <= datetime.now(timezone.utc):
        raise ValueError('Este cupón venció.')
    if coupon.used >= coupon.capacity:
        raise ValueError('Se agotaron los canjes de este cupón.')
    result = MenuService.quote(items)
    if result['has_errors'] or not result['lines']:
        raise ValueError('Revisa los productos de tu carrito.')
    subtotal = result['subtotal_cents']
    if coupon.kind == 'percent':
        discount = subtotal * coupon.percent // 100
        label = f'{coupon.percent}% de descuento'
    else:
        # Each complete group qualifies; cheapest units in the basket are free.
        units = sorted(price for row, item in zip(result['lines'], items) for price in [row['unit_cents']] * item['quantity'])
        free = (len(units) // coupon.take) * (coupon.take - coupon.pay)
        discount = sum(units[:free])
        label = f'Lleva {coupon.take}, paga {coupon.pay} (gratis los de menor precio)'
    if discount <= 0:
        raise ValueError('Tu carrito todavía no cumple esta promoción.')
    currency = MenuService.content().get('currency', 'USD')
    return dict(code=coupon.code, label=label, discount=money(discount, currency), total=money(subtotal-discount, currency), subtotal=result['formatted_subtotal'], lines=[dict(name=row['name'], quantity=item['quantity'], options=row['selection_labels'], unit=row['formatted_unit'], total=row['formatted_total']) for row, item in zip(result['lines'], items)])


@coupon_bp.post('/api/coupons/<action>')
@require_user()
def apply(action):
    if action not in ('preview', 'redeem', 'receipt'):
        abort(404)
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify(message='Solicitud inválida.'), 400
    code = str(data.get('code', '')).strip().upper()
    coupon = db.session.execute(db.select(Coupon).where(Coupon.code == code).with_for_update()).scalar_one_or_none()
    try:
        if not coupon:
            raise ValueError('Código de cupón inválido.')
        prior = CouponRedemption.query.filter_by(coupon_id=coupon.id, user_id=g.user.id).first()
        if prior and not prior.cancelled:
            if action in ('redeem', 'receipt'):
                return jsonify(**prior.snapshot, redemption=prior.id)
            raise ValueError('Ya canjeaste este cupón. Usa Recuperar canje para ver tu comprobante.')
        if action == 'receipt':
            raise ValueError('No tienes un canje activo para este código.')
        snapshot = offer(coupon, data.get('items'))
        if action == 'redeem':
            coupon.used += 1
            if prior:
                prior.id = str(uuid4())
                prior.snapshot = snapshot
                prior.cancelled = False
                prior.created_at = datetime.now(timezone.utc)
                redemption = prior
            else:
                redemption = CouponRedemption(id=str(uuid4()), coupon_id=coupon.id, user_id=g.user.id, snapshot=snapshot)
                db.session.add(redemption)
            db.session.commit()
            return jsonify(**snapshot, redemption=redemption.id)
        return jsonify(**snapshot)
    except (ValueError, MenuError) as error:
        db.session.rollback()
        return jsonify(message=str(error)), 400


@coupon_bp.route('/admin/cupones', methods=['GET', 'POST'])
@require_user('admin')
def admin():
    if request.method == 'POST':
        try:
            code = (request.form.get('code') or secrets.token_hex(4)).strip().upper()
            if not re.fullmatch(r'[A-Z0-9_-]{3,40}', code):
                raise ValueError('Usa de 3 a 40 letras, números, guiones o guiones bajos.')
            if Coupon.query.filter_by(code=code).first():
                raise ValueError('Este código ya existe.')
            kind = request.form.get('kind')
            percent, take, pay, capacity = [int(request.form.get(key, default)) for key, default in [('percent', 10), ('take', 3), ('pay', 2), ('capacity', 20)]]
            if capacity < 1 or capacity > 100000 or kind not in ('percent', 'bundle') or (kind == 'percent' and not 1 <= percent <= 100) or (kind == 'bundle' and not 1 <= pay < take <= 99):
                raise ValueError('Revisa porcentaje, unidades y cupos.')
            expires = datetime.fromisoformat(request.form['expires']).replace(tzinfo=timezone.utc) if request.form.get('expires') else None
            db.session.add(Coupon(code=code, kind=kind, percent=percent, take=take, pay=pay, capacity=capacity, expires=expires))
            db.session.commit()
            flash('Cupón creado.', 'success')
        except (ValueError, MenuError) as error:
            db.session.rollback()
            flash(str(error), 'error')
        return redirect(url_for('coupons.admin'))
    return render_template('pages/admin_coupons.html', coupons=Coupon.query.order_by(Coupon.id.desc()).all(), redemptions=CouponRedemption.query.order_by(CouponRedemption.created_at.desc()).limit(100).all())


@coupon_bp.post('/admin/cupones/<int:coupon_id>/toggle')
@require_user('admin')
def toggle(coupon_id):
    coupon = db.session.execute(db.select(Coupon).where(Coupon.id == coupon_id).with_for_update()).scalar_one_or_none()
    if not coupon:
        abort(404)
    coupon.active = not coupon.active
    db.session.commit()
    return redirect(url_for('coupons.admin'))


@coupon_bp.post('/admin/canjes/<redemption_id>/cancel')
@require_user('admin')
def cancel(redemption_id):
    redemption = db.session.get(CouponRedemption, redemption_id)
    if not redemption:
        abort(404)
    coupon = db.session.execute(db.select(Coupon).where(Coupon.id == redemption.coupon_id).with_for_update()).scalar_one()
    db.session.refresh(redemption)
    if not redemption.cancelled:
        redemption.cancelled = True
        coupon.used -= 1
        db.session.commit()
    return redirect(url_for('coupons.admin'))
