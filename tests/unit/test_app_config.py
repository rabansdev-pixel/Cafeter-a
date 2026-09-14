import pytest

from app import create_app
from app.core.config import DevelopmentConfig, ProductionConfig
from app.core.extensions import db
from app.models.product import Product
from app.services.product_service import ProductService


def test_production_requires_explicit_secret(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValueError, match="SECRET_KEY"):
        create_app("production")


def test_production_workers_share_configured_secret(monkeypatch):
    import secrets

    secret = secrets.token_hex(32)
    monkeypatch.setenv("SECRET_KEY", secret)
    monkeypatch.setattr(
        ProductionConfig, "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:"
    )
    first = create_app("production")
    second = create_app("production")
    assert first.secret_key == second.secret_key == secret
    assert "csrf" in first.extensions


def test_default_factory_seeds_database_once(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setattr(
        DevelopmentConfig, "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:"
    )
    app = create_app()
    with app.app_context():
        initial = [p.slug for p in Product.query.all()]
        assert len(initial) == 4
        ProductService().seed_initial_data()
        assert [p.slug for p in Product.query.all()] == initial


def test_internal_error_rolls_back_and_renders_page(monkeypatch):
    app = create_app("testing")
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.route("/broken")
    def broken():
        raise RuntimeError("simulated failure")

    calls = []
    rollback = db.session.rollback

    def record_rollback():
        calls.append(True)
        rollback()

    monkeypatch.setattr(db.session, "rollback", record_rollback)
    response = app.test_client().get("/broken")
    assert response.status_code == 500
    assert b"500" in response.data
    assert calls == [True]
