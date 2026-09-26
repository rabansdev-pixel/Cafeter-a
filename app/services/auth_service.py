"""Database-backed identities, server-side roles and signed sessions."""
from datetime import timedelta
from functools import wraps
from hashlib import sha256
import re
from flask import abort, g, has_request_context, jsonify, redirect, request, session, url_for
from sqlalchemy.dialects.postgresql import insert
from werkzeug.security import check_password_hash, generate_password_hash
from app.core.extensions import db
from app.models.identity import AccessAttempt, AuditLog, User, now

DUMMY_HASH = generate_password_hash('invalid-account-placeholder')


def init_auth(app):
    @app.before_request
    def load_user():
        g.user = None
        if request.endpoint in {'static', 'media.product_image'}:
            return
        uid = session.get('user_id')
        if type(uid) is int:
            user = db.session.get(User, uid)
            if user and user.active and user.session_version == session.get('user_version'):
                from app.services.firebase_service import enabled, session_valid, FirebaseError
                if user.firebase_uid:
                    try:
                        if not enabled() or not session_valid(user):
                            session.clear()
                            return
                    except FirebaseError:
                        return 'El servicio de acceso no está disponible. Inténtalo de nuevo en unos minutos.', 503
                elif enabled():
                    session.clear()
                    return
                g.user = user
            else:
                session.clear()

    @app.context_processor
    def identity_context():
        from app.services.firebase_service import public_config
        return {'current_user': g.get('user'), 'firebase_config': public_config()}

    @app.after_request
    def private_pages(response):
        if g.get('user') or request.path.startswith(('/login', '/registro', '/cuenta', '/admin', '/recuperar-acceso')):
            response.headers['Cache-Control'] = 'no-store'
        return response


def require_user(*roles):
    def decorator(view):
        @wraps(view)
        def guarded(*args, **kwargs):
            if not g.get('user'):
                if request.path.startswith('/api/'):
                    return jsonify(message='Inicia sesión.'), 401
                return redirect(url_for('main.login'))
            if roles and g.user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return guarded
    return decorator


def identity_fields(data, registration=True):
    email = str(data.get('email', '')).strip().lower()
    password = data.get('password', '')
    name = str(data.get('name', '')).strip()
    if len(email) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        raise ValueError('Introduce un correo válido.')
    if not isinstance(password, str) or len(password) > 256 or (registration and len(password) < 12):
        raise ValueError('Usa una contraseña de 12 a 256 caracteres.')
    if registration and not 1 <= len(name) <= 120:
        raise ValueError('Introduce tu nombre (máximo 120 caracteres).')
    return name, email, password


def throttle(namespace, value, limit):
    """Atomic shared rate limit; no emails or IP addresses are stored in plain text."""
    timestamp = now()
    key = sha256(f'{namespace}:{value}'.encode()).hexdigest()
    statement = insert(AccessAttempt).values(key=key, attempts=1, started_at=timestamp)
    from sqlalchemy import case
    expired = AccessAttempt.started_at < timestamp - timedelta(minutes=15)
    statement = statement.on_conflict_do_update(
        index_elements=['key'], set_={
            'attempts': case((expired, 1), else_=AccessAttempt.attempts + 1),
            'started_at': case((expired, timestamp), else_=AccessAttempt.started_at),
        }).returning(AccessAttempt.attempts)
    attempts = db.session.execute(statement).scalar_one()
    db.session.commit()
    return attempts <= limit


def authenticate(email, password):
    user = User.query.filter_by(email=email).first()
    valid = check_password_hash(user.password_hash if user and user.password_hash and not user.firebase_uid else DUMMY_HASH, password)
    if not valid or not user or not user.active or user.firebase_uid or not user.password_hash:
        return None
    session.clear()
    session['user_id'] = user.id
    session['user_version'] = user.session_version
    session.permanent = True
    return user


def audit(action, entity, entity_id, changes=None, actor_id=None):
    actor = g.get('user') if has_request_context() else None
    db.session.add(AuditLog(action=action, entity=entity, entity_id=entity_id,
                           changes=changes or {}, actor_id=actor_id or (actor.id if actor else None)))
