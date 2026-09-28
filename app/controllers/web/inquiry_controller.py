import secrets
from urllib.parse import urlencode
from flask import Blueprint, request, g, jsonify, render_template
from app.models import Inquiry, CouponRedemption
from app.core.extensions import db
from app.services.menu_service import MenuService, MenuError
from app.services.auth_service import require_user, throttle

inquiry_bp = Blueprint('inquiries', __name__)

@inquiry_bp.post('/api/inquiries')
def create():
    if not throttle('inquiry', request.remote_addr or '', 20):
        return jsonify(message='Espera unos minutos antes de volver a consultar.'), 429
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(message='Solicitud inválida.'), 400
    user = g.get('user')
    try:
        if data.get('redemption'):
            redemption = db.session.get(CouponRedemption, str(data['redemption']))
            if not user or not redemption or redemption.user_id != user.id or redemption.cancelled:
                raise ValueError('El canje no está disponible para esta cuenta.')
            snapshot = dict(redemption.snapshot, redemption=redemption.id)
        else:
            items = data.get('items')
            quote = MenuService.quote(items)
            if quote['has_errors'] or not quote['lines']:
                raise ValueError('Revisa los productos del carrito.')
            snapshot = dict(total=quote['formatted_subtotal'], lines=[dict(name=row['name'], quantity=item['quantity'], options=row['selection_labels'], total=row['formatted_total']) for row, item in zip(quote['lines'], items)])
        reference = 'ZD-' + secrets.token_hex(6).upper()
        customer = user.name if user else 'Invitado'
        record = Inquiry(reference=reference, user_id=user.id if user else None, customer=customer, snapshot=snapshot)
        db.session.add(record)
        db.session.commit()
        identity = f'{customer.split()[0] if customer.split() else "Cliente"} · Cuenta registrada' if user else 'Consulta como invitado'
        text = [f'Hola ZERO DAY · Consulta {reference}', identity]
        text += [f"{line['quantity']} × {line['name']} ({', '.join(line['options'])}) — {line['total']}" for line in snapshot['lines']]
        if snapshot.get('redemption'):
            text += [f"Canje: {snapshot['redemption']}", f"Cupón {snapshot['code']} · Descuento: {snapshot['discount']}"]
        text += [f"Total estimado: {snapshot['total']}", 'Pendiente de confirmar disponibilidad.']
        return jsonify(reference=reference, url='https://wa.me/593988357638?' + urlencode({'text':'\n'.join(text)}))
    except (ValueError, MenuError) as error:
        db.session.rollback()
        return jsonify(message=str(error)), 400

@inquiry_bp.get('/admin/consultas')
@require_user('admin', 'staff')
def admin():
    query = Inquiry.query
    reference = request.args.get('reference', '').strip().upper()
    if reference:
        query = query.filter_by(reference=reference)
    return render_template('pages/inquiries.html', records=query.order_by(Inquiry.created_at.desc()).limit(100).all(), admin=True)

@inquiry_bp.get('/cuenta/canjes')
@require_user()
def redemptions():
    return render_template('pages/inquiries.html', records=CouponRedemption.query.filter_by(user_id=g.user.id).order_by(CouponRedemption.created_at.desc()).all(), admin=False)
