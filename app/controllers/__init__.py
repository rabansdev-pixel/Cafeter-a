from app.controllers.web.main_controller import main_bp
from app.controllers.web.catalog_controller import catalog_bp
from app.controllers.api.products_api import products_api_bp
from app.controllers.api.cart_api import cart_api_bp
from app.controllers.api.health_api import health_bp

__all__ = ["main_bp", "catalog_bp", "products_api_bp", "cart_api_bp", "health_bp"]
