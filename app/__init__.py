import os
from flask import Flask, jsonify, render_template, request
from flask_wtf.csrf import CSRFError
from dotenv import load_dotenv

from app.core.config import config_by_name
from app.core.extensions import csrf, db, ma
from app.core.security import setup_security_headers
from app.controllers import (
    main_bp,
    catalog_bp,
    products_api_bp,
    cart_api_bp,
    health_bp,
)

load_dotenv()


def create_app(env_name=None):
    """
    Application Factory para crear la instancia de Flask
    según el entorno especificado ('development', 'testing', 'production').
    """
    if not env_name:
        env_name = os.getenv("APP_ENV", "development")

    config_class = config_by_name.get(env_name, config_by_name["default"])

    app = Flask(
        __name__,
        static_folder=config_class.STATIC_FOLDER,
        template_folder=config_class.TEMPLATES_FOLDER,
    )
    app.config.from_object(config_class())

    # Inicializar extensiones
    db.init_app(app)
    ma.init_app(app)
    csrf.init_app(app)

    # Configurar cabeceras de seguridad (SonarQube & Snyk)
    setup_security_headers(app)

    # Registrar Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(products_api_bp)
    app.register_blueprint(cart_api_bp)
    app.register_blueprint(health_bp)

    # Manejadores de errores personalizados
    @app.errorhandler(CSRFError)
    def csrf_error(error):
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    status="error",
                    message="Sesión inválida. Recarga la página.",
                ),
                400,
            )
        return error.get_response()

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("pages/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("pages/500.html"), 500

    # Inicialización de tablas y datos semilla
    with app.app_context():
        db.create_all()
        # Sembrar cafés en desarrollo o en la primera ejecución de producción.
        if env_name != "testing":
            from app.services.product_service import ProductService

            ProductService().seed_initial_data()

    return app
