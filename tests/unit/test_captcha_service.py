import json
import pytest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from flask import Flask
from app.services.captcha_service import verify, _normalize_host
from app.services.firebase_service import FirebaseError


@pytest.fixture
def test_app():
    app = Flask(__name__)
    app.config['RECAPTCHA_SITE_KEY'] = 'test-site-key'
    app.config['RECAPTCHA_PROJECT_ID'] = 'test-project'
    app.config['RECAPTCHA_API_KEY'] = 'test-api-key'
    app.config['RECAPTCHA_ALLOWED_HOSTS'] = ['cafeter-a-production.up.railway.app', 'localhost']
    return app


def test_normalize_host():
    assert _normalize_host('https://example.com/path') == 'example.com'
    assert _normalize_host('HTTP://MY-DOMAIN.COM:8080/') == 'my-domain.com'
    assert _normalize_host('localhost') == 'localhost'
    assert _normalize_host('') == ''


def test_verify_skips_when_no_site_key(test_app):
    test_app.config['RECAPTCHA_SITE_KEY'] = ''
    with test_app.app_context():
        # Debe retornar None sin lanzar error
        assert verify('any_token') is None


def test_verify_raises_if_not_configured(test_app):
    test_app.config['RECAPTCHA_API_KEY'] = ''
    with test_app.app_context():
        with pytest.raises(FirebaseError, match='Falta configurar'):
            verify('any_token')


def test_verify_raises_if_empty_token(test_app):
    with test_app.app_context():
        with pytest.raises(FirebaseError, match='Completa el captcha'):
            verify('')
        with pytest.raises(FirebaseError, match='Completa el captcha'):
            verify(None)


def test_verify_success_with_valid_token(test_app):
    response_data = {
        'tokenProperties': {
            'valid': True,
            'hostname': 'cafeter-a-production.up.railway.app'
        }
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_data).encode()
    mock_resp.__enter__.return_value = mock_resp

    with test_app.test_request_context(
        '/',
        headers={'Host': 'cafeter-a-production.up.railway.app', 'Referer': 'https://cafeter-a-production.up.railway.app/iniciar-sesion'}
    ):
        with patch('app.services.captcha_service.urlopen', return_value=mock_resp) as mock_urlopen:
            verify('valid_token_123')

            assert mock_urlopen.called
            req = mock_urlopen.call_args[0][0]
            assert req.headers.get('Referer') == 'https://cafeter-a-production.up.railway.app/iniciar-sesion'
            assert req.headers.get('X-goog-api-key') == 'test-api-key'
            assert 'key=test-api-key' in req.full_url


def test_verify_handles_http_error(test_app):
    mock_err = HTTPError(
        url='http://test',
        code=403,
        msg='Forbidden',
        hdrs={},
        fp=MagicMock(read=lambda: b'{"error": "Requests from this referer are blocked."}')
    )

    with test_app.test_request_context('/'):
        with patch('app.services.captcha_service.urlopen', side_effect=mock_err):
            with pytest.raises(FirebaseError, match='No se pudo verificar el captcha'):
                verify('token_that_fails_http')


def test_verify_rejects_invalid_token_assessment(test_app):
    response_data = {
        'tokenProperties': {
            'valid': False,
            'invalidReason': 'EXPIRED'
        }
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_data).encode()
    mock_resp.__enter__.return_value = mock_resp

    with test_app.test_request_context('/'):
        with patch('app.services.captcha_service.urlopen', return_value=mock_resp):
            with pytest.raises(FirebaseError, match='El captcha caducó o no es válido'):
                verify('expired_token')


def test_verify_rejects_mismatched_hostname(test_app):
    response_data = {
        'tokenProperties': {
            'valid': True,
            'hostname': 'malicious-domain.com'
        }
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_data).encode()
    mock_resp.__enter__.return_value = mock_resp

    with test_app.test_request_context('/'):
        with patch('app.services.captcha_service.urlopen', return_value=mock_resp):
            with pytest.raises(FirebaseError, match='El captcha caducó o no es válido'):
                verify('token_from_wrong_domain')
