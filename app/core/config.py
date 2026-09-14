import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _resolve_secret_key() -> str:
    """
    Retorna la clave secreta desde el entorno o genera un token criptográfico
    aleatorio en tiempo de ejecución para evitar secretos hardcodeados (Snyk CWE-798).
    """
    secret = os.getenv("SECRET_KEY")
    if not secret:
        secret = secrets.token_hex(32)
    return secret


class BaseConfig:
    """Configuración base común a todos los entornos."""

    SECRET_KEY = _resolve_secret_key()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STATIC_FOLDER = str(BASE_DIR / "app" / "static")
    TEMPLATES_FOLDER = str(BASE_DIR / "app" / "templates")
    JSON_AS_ASCII = False

    # Parámetros de negocio de la cafetería
    FREE_SHIPPING_THRESHOLD = float(os.getenv("FREE_SHIPPING_THRESHOLD", 50000.0))
    CURRENCY_SYMBOL = os.getenv("CURRENCY_SYMBOL", "$")

    def __init__(self):
        # Leer después de .env; los workers comparten la clave configurada.
        self.SECRET_KEY = _resolve_secret_key()


class DevelopmentConfig(BaseConfig):
    """Configuración para el entorno de desarrollo."""

    DEBUG = True
    TESTING = False
    ENV = "development"
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'dev_cafe.db'}"
    )


class TestingConfig(BaseConfig):
    """Configuración para el entorno de pruebas automatizadas (SonarQube & Pytest)."""

    DEBUG = False
    TESTING = True
    ENV = "testing"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    """Configuración para el entorno de producción endurecido."""

    DEBUG = False
    TESTING = False
    ENV = "production"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "")

    def __init__(self):
        super().__init__()
        # En producción se exige que SECRET_KEY esté explícita en el entorno
        if not os.getenv("SECRET_KEY"):
            raise ValueError(
                "CRÍTICO: Debes configurar la variable SECRET_KEY en producción."
            )


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
