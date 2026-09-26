import os
from datetime import timedelta
from sqlalchemy.engine import make_url
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _resolve_secret_key():
    secret = os.getenv("SECRET_KEY")
    if not secret or len(secret) < 32:
        raise ValueError("Configura SECRET_KEY con al menos 32 caracteres en el entorno.")
    return secret


class BaseConfig:
    """Configuración base común a todos los entornos."""

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    MAX_CONTENT_LENGTH = 9 * 1024 * 1024
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STATIC_FOLDER = str(BASE_DIR / "app" / "static")
    TEMPLATES_FOLDER = str(BASE_DIR / "app" / "templates")
    JSON_AS_ASCII = False

    # Parámetros de negocio de la cafetería
    FREE_SHIPPING_THRESHOLD = float(
        os.getenv("FREE_SHIPPING_THRESHOLD", 50000.0)
    )
    CURRENCY_SYMBOL = os.getenv("CURRENCY_SYMBOL", "$")

    def __init__(self):
        # Leer después de .env; los workers comparten la clave configurada.
        self.SECRET_KEY = _resolve_secret_key()
        self.AUTH_PROVIDER = os.getenv('AUTH_PROVIDER', 'local').strip().lower()
        self.FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY', '').strip()
        self.FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', '').strip()
        self.FIREBASE_AUTH_DOMAIN = os.getenv('FIREBASE_AUTH_DOMAIN', f'{self.FIREBASE_PROJECT_ID}.firebaseapp.com').strip()
        self.RECAPTCHA_SITE_KEY = os.getenv('RECAPTCHA_SITE_KEY', '').strip()
        self.RECAPTCHA_PROJECT_ID = os.getenv('RECAPTCHA_PROJECT_ID', self.FIREBASE_PROJECT_ID).strip()
        self.RECAPTCHA_API_KEY = os.getenv('RECAPTCHA_API_KEY', '').strip()
        self.RECAPTCHA_ALLOWED_HOSTS = [host.strip() for host in os.getenv('RECAPTCHA_ALLOWED_HOSTS', '').split(',') if host.strip()]
        self.FIREBASE_APP_ID = os.getenv('FIREBASE_APP_ID', '').strip()
        if self.AUTH_PROVIDER not in {'local', 'firebase'}:
            raise ValueError('AUTH_PROVIDER debe ser local o firebase.')
        if self.AUTH_PROVIDER == 'firebase' and not (self.FIREBASE_API_KEY and self.FIREBASE_PROJECT_ID):
            raise ValueError('Configura FIREBASE_API_KEY y FIREBASE_PROJECT_ID en el entorno.')
        uri = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://", 1)
        try:
            parsed = make_url(uri)
            if parsed.drivername not in {"postgresql", "postgresql+psycopg2"} or not parsed.database:
                raise ValueError()
        except Exception:
            raise ValueError("DATABASE_URL debe ser una conexión PostgreSQL válida.") from None
        self.SQLALCHEMY_DATABASE_URI = uri
        self.SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "connect_args": {"connect_timeout": 10}}
        self.SESSION_COOKIE_SECURE = self.ENV == "production"


class DevelopmentConfig(BaseConfig):
    """Configuración para el entorno de desarrollo."""

    DEBUG = True
    TESTING = False
    ENV = "development"


class TestingConfig(BaseConfig):
    """Configuración para pruebas automatizadas (SonarQube y Pytest)."""

    DEBUG = False
    TESTING = True
    ENV = "testing"

    def __init__(self):
        super().__init__()
        # Existing fixtures drop all tables. Never allow them against the store DB.
        if os.getenv("ALLOW_DATABASE_TESTS") != "1" or not make_url(self.SQLALCHEMY_DATABASE_URI).database.endswith("_test"):
            raise ValueError("Las pruebas requieren una base desechable terminada en _test y ALLOW_DATABASE_TESTS=1.")


class ProductionConfig(BaseConfig):
    """Configuración para el entorno de producción endurecido."""

    DEBUG = False
    TESTING = False
    ENV = "production"

    def __init__(self):
        super().__init__()
        # En producción se exige que SECRET_KEY esté explícita en el entorno
        if not os.getenv("SECRET_KEY"):
            raise ValueError(
                "CRÍTICO: Configura la variable SECRET_KEY en producción."
            )


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
