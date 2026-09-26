"""Real account/admin handlers, retaining the existing main blueprint endpoints."""
from flask import abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash
from app.core.extensions import db
from app.models import Product, Category, User, AuditLog
from app.services.auth_service import require_user, identity_fields, authenticate, throttle, audit
from app.services.store_service import save_product, deactivate_product
from app.services.image_service import store_image
from app.services import firebase_service as firebase
from app.services.captcha_service import verify as verify_captcha


def access():
    mode = {'/registro': 'register', '/recuperar-acceso': 'recover'}.get(request.path, 'login')
    if g.get('user'):
        return redirect(url_for('main.account_preview'))
    status = 200
    if request.method == 'POST' and mode == 'recover':
        try:
            _, email, _ = identity_fields(dict(email=request.form.get('email'), password=''), registration=False)
            if not throttle('reset-ip', request.remote_addr or '', 8) or not throttle('reset-email', email, 3):
                flash('Demasiados intentos. Espera 15 minutos.', 'error')
                return render_template('pages/access.html', mode=mode), 429
            if not firebase.enabled():
                flash('La recuperación por correo todavía no está configurada.', 'error')
                return render_template('pages/access.html', mode=mode), 503
            verify_captcha(request.form.get('g-recaptcha-response'))
            firebase.send_reset(email)
            flash('Si el correo tiene una cuenta en Firebase, recibirás un enlace para recuperar el acceso.', 'success')
            return redirect(url_for('main.login'), code=303)
        except firebase.FirebaseError as error:
            flash(str(error), 'error')
            status = error.status
        except ValueError as error:
            flash(str(error), 'error')
            status = 400
    elif request.method == 'POST':
        try:
            name, email, password = identity_fields(request.form, registration=mode == 'register')
            if not throttle('access-ip', request.remote_addr or '', 40) or not throttle('access-email', email, 10):
                flash('Demasiados intentos. Espera 15 minutos.', 'error')
                return render_template('pages/access.html', mode=mode), 429
            verify_captcha(request.form.get('g-recaptcha-response'))
            if firebase.enabled():
                if mode == 'register':
                    firebase.register(name, email, password)
                    flash('Cuenta creada. Ya puedes iniciar sesión.', 'success')
                    return redirect(url_for('main.login'), code=303)
                user = firebase.password_login(email, password)
                return redirect(url_for('main.admin_preview' if user.role in ('admin', 'staff') else 'main.account_preview'), code=303)
            if mode == 'register':
                user = User(name=name, email=email, password_hash=generate_password_hash(password), role='customer')
                db.session.add(user)
                db.session.flush()
                audit('user.register', 'user', user.id, actor_id=user.id)
                db.session.commit()
                flash('Cuenta creada. Ya puedes iniciar sesión.', 'success')
                return redirect(url_for('main.login'), code=303)
            user = authenticate(email, password)
            if user:
                return redirect(url_for('main.admin_preview' if user.role in ('admin', 'staff') else 'main.account_preview'), code=303)
            flash('Correo o contraseña incorrectos.', 'error')
            status = 401
        except firebase.FirebaseError as error:
            db.session.rollback()
            flash(str(error), 'error')
            status = error.status
        except ValueError as error:
            flash(str(error), 'error')
            status = 400
        except IntegrityError:
            db.session.rollback()
            flash('No se pudo crear la cuenta. Si ya tienes una, inicia sesión.', 'error')
            status = 400
    return render_template('pages/access.html', mode=mode), status


@require_user()
def account():
    return render_template('pages/account_preview.html')


@require_user()
def logout():
    firebase.end_session()
    return redirect(url_for('main.login'), code=303)


@require_user('admin', 'staff')
def admin():
    section = request.args.get('section', 'dashboard')
    if section not in {'dashboard', 'products', 'categories', 'inventory', 'users', 'activity'}:
        abort(404)
    if section in ('users', 'activity') and g.user.role != 'admin':
        abort(403)
    products = Product.query.filter(Product.menu_id.isnot(None)).order_by(Product.category_id, Product.position, Product.id).all()
    from app.services.dashboard_service import dashboard_data
    return render_template('pages/admin_preview.html', section=section, products=products,
        dashboard=dashboard_data(section, products),
        categories=Category.query.order_by(Category.position, Category.id).all(),
        users=User.query.order_by(User.id).limit(200).all() if section == 'users' else [],
        activity=AuditLog.query.order_by(AuditLog.id.desc()).limit(100).all() if section == 'activity' else [])


@require_user('admin', 'staff')
def product_edit(product_id=None):
    product = db.get_or_404(Product, product_id) if product_id else None
    if product and not product.menu_id:
        abort(404)
    status = 200
    if request.method == 'POST':
        data = {k: request.form.get(k, '') for k in ('name', 'slug', 'description', 'tagline', 'price', 'category_id', 'image', 'stock')}
        data['active'] = request.form.get('active') == 'on'
        try:
            upload = request.files.get('image_file')
            if upload and upload.filename:
                data['image'] = store_image(upload)
            elif not data['image'] and product:
                data['image'] = product.image
            save_product(data, product)
            flash('Producto guardado.', 'success')
            return redirect(url_for('main.admin_preview'), code=303)
        except ValueError as error:
            db.session.rollback()
            flash(str(error), 'error')
            status = 400
        except IntegrityError:
            db.session.rollback()
            flash('No se pudo guardar: revisa el slug y los datos del producto.', 'error')
            status = 409
    return render_template('pages/admin_product.html', product=product,
        categories=Category.query.order_by(Category.position, Category.id).all()), status


@require_user('admin', 'staff')
def product_delete(product_id):
    product = db.get_or_404(Product, product_id)
    if not product.menu_id:
        abort(404)
    deactivate_product(product)
    flash('Producto desactivado. Puedes volver a activarlo al editarlo.', 'success')
    return redirect(url_for('main.admin_preview'), code=303)


@require_user('admin')
def user_update(user_id):
    # Protect the last administrator, including concurrent requests.
    db.session.execute(text('SELECT pg_advisory_xact_lock(2409202602)'))
    user = db.get_or_404(User, user_id)
    role, active = request.form.get('role'), request.form.get('active') == 'on'
    if role not in ('customer', 'staff', 'admin'):
        abort(400)
    if user.id == g.user.id and (role != 'admin' or not active):
        flash('No puedes quitarte tu propio acceso administrativo.', 'error')
        db.session.rollback()
    elif user.role == 'admin' and user.active and (role != 'admin' or not active) and User.query.filter_by(role='admin', active=True).count() <= 1:
        flash('Debe quedar al menos un administrador activo.', 'error')
        db.session.rollback()
    else:
        before = dict(role=user.role, active=user.active)
        user.role, user.active = role, active
        user.session_version += 1
        audit('user.permissions', 'user', user.id, {'before': before, 'after': dict(role=role, active=active)})
        db.session.commit()
        if user.id == g.user.id:
            session['user_version'] = user.session_version
        flash('Permisos actualizados; las sesiones anteriores se han invalidado.', 'success')
    return redirect(url_for('main.admin_preview', section='users'), code=303)


def firebase_session():
    if not firebase.enabled():
        return jsonify(message='Firebase no está configurado.'), 503
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(message='Solicitud inválida.'), 400
    password = data.get('legacy_password', '')
    if not isinstance(password, str) or len(password) > 256:
        return jsonify(message='Contraseña inválida.'), 400
    if not throttle('firebase-ip', request.remote_addr or '', 30):
        return jsonify(message='Demasiados intentos. Espera 15 minutos.'), 429
    try:
        verify_captcha(data.get('captcha_token'))
        user = firebase.establish_session(data.get('id_token'), password)
        target = 'main.admin_preview' if user.role in ('admin', 'staff') else 'main.account_preview'
        return jsonify(redirect=url_for(target))
    except firebase.FirebaseError as error:
        db.session.rollback()
        return jsonify(message=str(error), code=error.code), error.status
    except IntegrityError:
        db.session.rollback()
        return jsonify(message='La cuenta cambió durante el acceso. Vuelve a iniciar sesión.'), 409
