"""Server-side verification for the Enterprise checkbox (never trust the widget alone)."""
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from flask import current_app, has_request_context, request as flask_request
from app.services.firebase_service import FirebaseError


def _normalize_host(value):
    if not value or not isinstance(value, str):
        return ''
    cleaned = value.lower().strip().strip("'\"")
    if '://' in cleaned:
        cleaned = cleaned.split('://', 1)[1]
    cleaned = cleaned.split('/', 1)[0]
    cleaned = cleaned.split(':', 1)[0]
    return cleaned


def verify(token):
    config = current_app.config
    site_key = config.get('RECAPTCHA_SITE_KEY')
    if not site_key:
        return
    project = config.get('RECAPTCHA_PROJECT_ID', '')
    api_key = config.get('RECAPTCHA_API_KEY', '')
    raw_hosts = config.get('RECAPTCHA_ALLOWED_HOSTS', [])

    clean_hosts = {_normalize_host(h) for h in raw_hosts if _normalize_host(h)}

    if not api_key or not re.fullmatch(r'[a-z0-9-]+', project) or not clean_hosts:
        raise FirebaseError('Falta configurar la verificación del captcha en el servidor.', status=503)
    if not isinstance(token, str) or not token or len(token) > 16384:
        raise FirebaseError('Completa el captcha antes de continuar.', status=400)

    # Determinar el Referer requerido cuando la API Key tiene restricciones en Google Cloud
    referer = None
    if has_request_context():
        req_host = _normalize_host(flask_request.host)
        if req_host:
            clean_hosts.add(req_host)
        candidate_ref = flask_request.referrer or flask_request.headers.get('Referer')
        if candidate_ref:
            ref_host = _normalize_host(candidate_ref)
            if ref_host in clean_hosts:
                referer = candidate_ref
        if not referer and flask_request.host_url:
            referer = flask_request.host_url

    if not referer:
        for h in sorted(clean_hosts):
            if h not in ('localhost', '127.0.0.1'):
                referer = f'https://{h}/'
                break
        if not referer and clean_hosts:
            first = next(iter(clean_hosts))
            referer = f'http://{first}/' if first in ('localhost', '127.0.0.1') else f'https://{first}/'

    body = json.dumps({'event': {'token': token, 'siteKey': site_key}}).encode()
    url = f'https://recaptchaenterprise.googleapis.com/v1/projects/{project}/assessments?key={api_key}'
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': api_key,
        'User-Agent': 'Mozilla/5.0 (compatible; CafeteriaVerification/1.0)',
    }
    if referer:
        headers['Referer'] = referer

    req = Request(url, data=body, headers=headers, method='POST')
    try:
        with urlopen(req, timeout=10) as response:
            result = json.load(response)
    except HTTPError as err:
        err_msg = ''
        try:
            err_msg = err.read().decode('utf-8', errors='replace')
        except Exception:
            err_msg = str(err)
        current_app.logger.warning('reCAPTCHA assessment falló con HTTP %s: %s', err.code, err_msg)
        raise FirebaseError('No se pudo verificar el captcha. Inténtalo de nuevo.', status=503) from None
    except (URLError, TimeoutError, ValueError) as err:
        current_app.logger.warning('reCAPTCHA assessment falló por error de red/parseo: %s', err)
        raise FirebaseError('No se pudo verificar el captcha. Inténtalo de nuevo.', status=503) from None

    properties = result.get('tokenProperties', {}) if isinstance(result, dict) else {}
    token_valid = isinstance(properties, dict) and properties.get('valid') is True
    token_host = _normalize_host(properties.get('hostname', ''))

    if not token_valid:
        invalid_reason = properties.get('invalidReason', 'DESCONOCIDO') if isinstance(properties, dict) else 'DESCONOCIDO'
        current_app.logger.info('reCAPTCHA token no válido: reason=%s', invalid_reason)
        raise FirebaseError('El captcha caducó o no es válido. Complétalo otra vez.', status=400)

    if token_host not in clean_hosts:
        current_app.logger.warning('reCAPTCHA hostname no autorizado (%s). Permitidos: %s', token_host, clean_hosts)
        raise FirebaseError('El captcha caducó o no es válido. Complétalo otra vez.', status=400)

