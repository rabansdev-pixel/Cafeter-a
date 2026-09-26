"""Server-side verification for the Enterprise checkbox (never trust the widget alone)."""
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from flask import current_app
from app.services.firebase_service import FirebaseError


def verify(token):
    config = current_app.config
    site_key = config.get('RECAPTCHA_SITE_KEY')
    if not site_key:
        return
    project = config.get('RECAPTCHA_PROJECT_ID', '')
    api_key = config.get('RECAPTCHA_API_KEY', '')
    hosts = config.get('RECAPTCHA_ALLOWED_HOSTS', [])
    if not api_key or not re.fullmatch(r'[a-z0-9-]+', project) or not hosts:
        raise FirebaseError('Falta configurar la verificación del captcha en el servidor.', status=503)
    if not isinstance(token, str) or not token or len(token) > 16384:
        raise FirebaseError('Completa el captcha antes de continuar.', status=400)
    body = json.dumps({'event': {'token': token, 'siteKey': site_key}}).encode()
    request = Request(
        f'https://recaptchaenterprise.googleapis.com/v1/projects/{project}/assessments',
        data=body, headers={'Content-Type': 'application/json', 'X-Goog-Api-Key': api_key},
        method='POST',
    )
    try:
        with urlopen(request, timeout=10) as response:
            result = json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError):
        raise FirebaseError('No se pudo verificar el captcha. Inténtalo de nuevo.', status=503) from None
    properties = result.get('tokenProperties', {}) if isinstance(result, dict) else {}
    if not isinstance(properties, dict) or properties.get('valid') is not True or properties.get('hostname') not in hosts:
        raise FirebaseError('El captcha caducó o no es válido. Complétalo otra vez.', status=400)
