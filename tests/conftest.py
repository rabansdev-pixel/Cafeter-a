import pytest
from app import create_app
from app.core.extensions import db
from app.services.product_service import ProductService


@pytest.fixture(scope="session")
def app():
    """Fixture de la aplicación Flask en entorno 'testing'."""
    test_app = create_app("testing")

    with test_app.app_context():
        db.create_all()
        # Sembrar datos iniciales de prueba
        ProductService().seed_initial_data()
        yield test_app
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Cliente HTTP para pruebas de endpoints y vistas."""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """Runner para comandos CLI de Flask."""
    return app.test_cli_runner()
