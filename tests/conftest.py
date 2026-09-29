import re
import os
import secrets
from sqlalchemy.engine import make_url

import pytest
from app import create_app
from app.core.extensions import db
from app.services.product_service import ProductService


@pytest.fixture(scope="session", autouse=True)
def isolated_test_environment():
    # Never reuse DATABASE_URL from .env: fixtures create/drop tables.
    uri = os.environ.get('TEST_DATABASE_URL', '')
    if not uri:
        raise pytest.UsageError('Set TEST_DATABASE_URL to a disposable local PostgreSQL database ending in _test.')
    parsed = make_url(uri)
    if parsed.get_backend_name() != 'postgresql' or parsed.host not in {'localhost', '127.0.0.1'} or not (parsed.database or '').endswith('_test'):
        raise pytest.UsageError('Tests require local PostgreSQL and a database ending in _test.')
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv('DATABASE_URL', uri)
        patch.setenv('SECRET_KEY', secrets.token_hex(32))
        patch.setenv('ALLOW_DATABASE_TESTS', '1')
        patch.setenv('AUTH_PROVIDER', 'local')
        patch.setenv('RECAPTCHA_SITE_KEY', '')
        yield


@pytest.fixture(scope="session")
def app(isolated_test_environment):
    """Fixture de la aplicación Flask en entorno 'testing'."""
    test_app = create_app("testing")

    with test_app.app_context():
        db.create_all()
        # Sembrar datos iniciales de prueba
        ProductService().seed_initial_data()
    yield test_app
    with test_app.app_context():
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Cliente HTTP para pruebas de endpoints y vistas."""
    return app.test_client()


@pytest.fixture
def csrf_headers(client):
    page = client.get("/").get_data(as_text=True)
    token = re.search(r'name="csrf-token" content="([^"]+)"', page).group(1)
    return {"X-CSRFToken": token}


@pytest.fixture(scope="function")
def runner(app):
    """Runner para comandos CLI de Flask."""
    return app.test_cli_runner()
