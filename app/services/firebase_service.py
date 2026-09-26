"""Firebase authenticates identities; PostgreSQL alone authorizes local roles."""
import base64
import json
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import requests
from cachecontrol import CacheControl
from cryptography.fernet import Fernet, InvalidToken
from flask import current_app, session
from google.auth.exceptions import TransportError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.id_token import verify_firebase_token
from werkzeug.security import check_password_hash
from app.core.extensions import db
from app.models import User
from app.models.firebase_session import FirebaseSession
from app.models.identity import now
from app.services.auth_service import audit

# Public signing certificates honor Google's cache headers instead of a new fetch per login.
_certificates = GoogleRequest(session=CacheControl(requests.Session()))


class FirebaseError(ValueError):
    def __init__(self, message, code='AUTH_ERROR', status=400):
        super().__init__(message)
        self.code, self.status = code, status


def enabled():
    return current_app.config['AUTH_PROVIDER'] == 'firebase'


def public_config():
    if not enabled():
        return None
    return dict(apiKey=current_app.config['FIREBASE_API_KEY'],
                projectId=current_app.config['FIREBASE_PROJECT_ID'],
                authDomain=current_app.config['FIREBASE_AUTH_DOMAIN'],
                appId=current_app.config['FIREBASE_APP_ID'])


def _api(method, payload):
    """Only fixed Google endpoints; never log passwords, tokens or response bodies."""
    query = urlencode({'key': current_app.config['FIREBASE_API_KEY']})
    request = Request(f'https://identitytoolkit.googleapis.com/v1/accounts:{method}?{query}',
        data=json.dumps(payload).encode(), headers={'Content-Type':'application/json', 'X-Firebase-Locale':'es'})
    try:
        with urlopen(request, timeout=12) as response:
            result = json.load(response)
        if not isinstance(result, dict):
            raise FirebaseError('Firebase devolvió una respuesta inválida.', status=502)
        return result
    except HTTPError as error:
        try:
            code = json.loads(error.read(16384)).get('error', {}).get('message', '').split(' : ')[0]
        except (ValueError, AttributeError):
            code = ''
        messages = {
            'OPERATION_NOT_ALLOWED': ('Activa Correo electrónico/contraseña en Firebase Authentication.', 503),
            'PASSWORD_LOGIN_DISABLED': ('El acceso con contraseña está deshabilitado en Firebase.', 503),
            'CONFIGURATION_NOT_FOUND': ('Configura Firebase Authentication antes de iniciar sesión.', 503),
            'API_KEY_INVALID': ('La configuración de Firebase necesita revisión.', 503),
            'TOO_MANY_ATTEMPTS_TRY_LATER': ('Demasiados intentos. Espera unos minutos.', 429),
            'QUOTA_EXCEEDED': ('El servicio de acceso alcanzó su límite. Inténtalo más tarde.', 503),
            'WEAK_PASSWORD': ('Firebase requiere una contraseña más segura.', 400),
            'PASSWORD_DOES_NOT_MEET_REQUIREMENTS': ('La contraseña no cumple la política de Firebase.', 400),
        }
        message, status = messages.get(code, ('No se pudo completar el acceso. Revisa tus datos.', 401))
        raise FirebaseError(message, code, status) from None
    except (URLError, TimeoutError, OSError, ValueError) as error:
        if isinstance(error, FirebaseError):
            raise
        raise FirebaseError('No se pudo conectar con Firebase. Inténtalo de nuevo.', 'UNAVAILABLE', 503) from None


def _certificate_request(*args, **kwargs):
    kwargs.setdefault('timeout', 8)
    return _certificates(*args, **kwargs)


def identity(token, fresh=True):
    if not isinstance(token, str) or not 1 <= len(token) <= 16384:
        raise FirebaseError('Sesión inválida.', status=401)
    project = current_app.config['FIREBASE_PROJECT_ID']
    try:
        claims = verify_firebase_token(token, _certificate_request, audience=project, clock_skew_in_seconds=30)
    except TransportError:
        raise FirebaseError('No se pudo verificar el acceso con Google.', 'UNAVAILABLE', 503) from None
    except (ValueError, TypeError):
        raise FirebaseError('La sesión de Firebase no es válida o ha caducado.', status=401) from None
    timestamp = now().timestamp()
    uid = claims.get('sub')
    auth_time = claims.get('auth_time')
    provider = claims.get('firebase', {}).get('sign_in_provider')
    if (claims.get('iss') != f'https://securetoken.google.com/{project}' or
        not isinstance(uid, str) or not 1 <= len(uid) <= 128 or
        not isinstance(auth_time, (int, float)) or auth_time > timestamp + 30 or
        (fresh and timestamp - auth_time > 300) or provider not in {'password', 'google.com'}):
        raise FirebaseError('Vuelve a iniciar sesión para continuar.', status=401)
    record = account_record(token, uid, auth_time)
    email = record.get('email', '').strip().lower()
    if not email or len(email) > 254 or email != str(claims.get('email', '')).strip().lower():
        raise FirebaseError('La cuenta no tiene un correo válido. Vuelve a iniciar sesión.', status=401)
    if provider == 'google.com' and (claims.get('email_verified') is not True or record.get('emailVerified') is not True):
        raise FirebaseError('Verifica el correo de tu cuenta de Google.', status=401)
    return dict(uid=uid, email=email, name=str(record.get('displayName') or '').strip()[:120],
                auth_time=auth_time, expires=int(claims['exp']))


def account_record(token, uid, auth_time):
    records = _api('lookup', {'idToken': token}).get('users', [])
    if not records or records[0].get('localId') != uid:
        raise FirebaseError('La cuenta ya no está disponible.', status=401)
    record = records[0]
    try:
        revoked = float(record.get('validSince', 0)) > auth_time
    except (ValueError, TypeError):
        revoked = True
    if record.get('disabled') or revoked:
        raise FirebaseError('Tu sesión ha caducado. Vuelve a iniciar sesión.', status=401)
    return record


def _cipher():
    # Domain-separated key derived from the stable server secret. No token in cookies.
    key = sha256(('zero-day/firebase/v1:' + current_app.config['SECRET_KEY']).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def bind_user(profile, legacy_password='', name=''):
    user = User.query.filter_by(firebase_uid=profile['uid']).first()
    if user:
        if not user.active or user.email != profile['email']:
            raise FirebaseError('La cuenta necesita revisión del administrador.', status=403)
        return user
    user = User.query.filter_by(email=profile['email']).with_for_update().first()
    if user:
        if not user.active or user.firebase_uid:
            raise FirebaseError('No se puede vincular esta cuenta.', status=403)
        # Matching an email is never enough to inherit staff/admin privileges.
        if not user.password_hash or not check_password_hash(user.password_hash, legacy_password):
            raise FirebaseError('Escribe tu contraseña anterior de ZERO DAY y vuelve a pulsar Continuar con Google para vincular tu cuenta.', 'LINK_REQUIRED', 409)
        user.firebase_uid = profile['uid']
        user.password_hash = None
        user.session_version += 1
        audit('user.firebase_link', 'user', user.id, actor_id=user.id)
    else:
        user = User(email=profile['email'], name=(name or profile['name'] or 'Cliente')[:120],
                    firebase_uid=profile['uid'], password_hash=None, role='customer')
        db.session.add(user)
        db.session.flush()
        audit('user.register', 'user', user.id, actor_id=user.id)
    db.session.flush()
    return user


def establish_session(token, legacy_password='', name=''):
    profile = identity(token)
    user = bind_user(profile, legacy_password, name)
    timestamp = now()
    expiry = datetime.fromtimestamp(profile['expires'], timezone.utc)
    record = FirebaseSession(user_id=user.id, user_version=user.session_version,
        encrypted_tokens=_cipher().encrypt(token.encode()).decode(),
        authenticated_at=datetime.fromtimestamp(profile['auth_time'], timezone.utc),
        token_expires_at=expiry, expires_at=min(expiry, timestamp + timedelta(hours=1)), checked_at=timestamp)
    db.session.add(record)
    # Remove expired tokens at successful login; don't retain credentials indefinitely.
    db.session.execute(db.delete(FirebaseSession).where(FirebaseSession.expires_at < timestamp))
    db.session.commit()
    session.clear()
    session['user_id'] = user.id
    session['user_version'] = user.session_version
    session['firebase_session_id'] = record.id
    session.permanent = True
    return user


def session_valid(user):
    session_id = session.get('firebase_session_id')
    if not isinstance(session_id, str):
        return False
    record = db.session.get(FirebaseSession, session_id)
    timestamp = now()
    if not record or record.user_id != user.id or record.user_version != user.session_version or record.expires_at <= timestamp:
        return False
    if record.checked_at < timestamp - timedelta(minutes=5):
        try:
            token = _cipher().decrypt(record.encrypted_tokens.encode()).decode()
            account = account_record(token, user.firebase_uid, record.authenticated_at.timestamp())
            if account.get('email', '').strip().lower() != user.email:
                return False
        except InvalidToken:
            return False
        except FirebaseError as error:
            if error.status == 503:
                raise
            return False
        record.checked_at = timestamp
        db.session.commit()
    return True


def end_session():
    session_id = session.get('firebase_session_id')
    if isinstance(session_id, str):
        db.session.execute(db.delete(FirebaseSession).where(FirebaseSession.id == session_id, FirebaseSession.user_id == session.get('user_id')))
        db.session.commit()
    session.clear()


def password_login(email, password):
    local = User.query.filter_by(email=email).first()
    if local and not local.active:
        raise FirebaseError('Correo o contraseña incorrectos.', status=401)
    legacy = local and not local.firebase_uid and local.password_hash and check_password_hash(local.password_hash, password)
    try:
        result = _api('signInWithPassword', {'email':email, 'password':password, 'returnSecureToken':True})
    except FirebaseError as error:
        if not legacy or error.code not in {'EMAIL_NOT_FOUND', 'INVALID_LOGIN_CREDENTIALS', 'INVALID_PASSWORD'}:
            raise
        # First successful old-password login migrates the existing account lazily.
        try:
            result = _api('signUp', {'email':email, 'password':password, 'returnSecureToken':True})
        except FirebaseError as signup_error:
            if signup_error.code == 'EMAIL_EXISTS':
                raise FirebaseError('Ese correo ya tiene otro acceso en Firebase. Usa Google y tu contraseña anterior para vincularlo.', 'LINK_REQUIRED', 409) from None
            raise
    return establish_session(result.get('idToken'), password)


def register(name, email, password):
    if User.query.filter_by(email=email).first():
        raise FirebaseError('No se pudo crear la cuenta. Si ya tienes una, inicia sesión.', status=409)
    result = _api('signUp', {'email':email, 'password':password, 'returnSecureToken':True})
    profile = identity(result.get('idToken'))
    user = bind_user(profile, name=name)
    # Persist the real profile; sign-in creates the browser's session separately.
    db.session.commit()
    return user


def send_reset(email):
    try:
        _api('sendOobCode', {'requestType':'PASSWORD_RESET', 'email':email})
    except FirebaseError as error:
        if error.code != 'EMAIL_NOT_FOUND':
            raise
