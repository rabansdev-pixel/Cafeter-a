import nh3
from flask import Blueprint, jsonify, request
from app.services.product_service import ProductService
from app.schemas.product_schema import products_schema, product_schema

products_api_bp = Blueprint("products_api", __name__, url_prefix="/api/products")
product_service = ProductService()


@products_api_bp.route("", methods=["GET"])
def list_products():
    """
    Endpoint REST con soporte de filtros por tueste y país de origen con sanitización.
    """
    raw_roast = request.args.get("roast", "")
    raw_country = request.args.get("country", "")

    # Sanitización de parámetros para prevenir inyección de caracteres maliciosos o XSS
    roast = nh3.clean(raw_roast.strip()) if raw_roast else None
    country = nh3.clean(raw_country.strip()) if raw_country else None

    products = product_service.get_catalog(roast=roast, country=country)
    return (
        jsonify(
            {
                "status": "success",
                "count": len(products),
                "data": products_schema.dump(products),
            }
        ),
        200,
    )


@products_api_bp.route("/<int:product_id>/radar", methods=["GET"])
def get_radar(product_id):
    """Devuelve los datos del radar sensorial para visualización SVG/Canvas."""
    radar_data = product_service.get_radar_data(product_id)
    if not radar_data:
        return (
            jsonify({"status": "error", "message": "Producto o perfil no encontrado"}),
            404,
        )
    return jsonify({"status": "success", "data": radar_data}), 200


@products_api_bp.route("/<slug>", methods=["GET"])
def get_product(slug):
    """Detalle de un producto individual en JSON con sanitización del slug."""
    clean_slug = nh3.clean(slug.strip())
    product = product_service.get_by_slug(clean_slug)
    if not product:
        return jsonify({"status": "error", "message": "Café no encontrado"}), 404
    return jsonify({"status": "success", "data": product_schema.dump(product)}), 200
