import nh3
from flask import Blueprint, jsonify, request
from app.services.product_service import ProductService
from app.schemas.product_schema import product_schema

# Authenticated CRUD shares exactly the same validation as the admin forms.
from app.core.extensions import db
from app.models import Product
from app.services.auth_service import require_user
from app.services.store_service import save_product, deactivate_product, product_data
from sqlalchemy.exc import IntegrityError


products_api_bp = Blueprint("products_api", __name__, url_prefix="/api/products")
product_service = ProductService()


@products_api_bp.route("", methods=["GET"])
def list_products():
    """Published store products. The legacy sensory radar keeps its own endpoint."""
    products = Product.query.filter(Product.menu_id.isnot(None), Product.is_active.is_(True)).order_by(Product.category_id, Product.position, Product.id).all()
    return jsonify(status="success", count=len(products), data=[product_data(product) for product in products])


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
    return jsonify({"status": "success", "data": product_data(product) if product.menu_id else product_schema.dump(product)}), 200

@products_api_bp.route('/manage', methods=['GET'])
@require_user('admin', 'staff')
def manage_products():
    products = Product.query.filter(Product.menu_id.isnot(None)).order_by(Product.id).all()
    return jsonify(data=[product_data(product) for product in products])


@products_api_bp.route('', methods=['POST'])
@require_user('admin', 'staff')
def create_product():
    return write_product()


@products_api_bp.route('/<int:product_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
@require_user('admin', 'staff')
def manage_product(product_id):
    product = db.get_or_404(Product, product_id)
    if not product.menu_id:
        return jsonify(message='Este producto no pertenece a la tienda.'), 404
    if request.method == 'GET':
        return jsonify(data=product_data(product))
    if request.method == 'DELETE':
        deactivate_product(product)
        return '', 204
    return write_product(product)


def write_product(product=None):
    try:
        created = product is None
        product = save_product(request.get_json(silent=True), product)
        return jsonify(data=product_data(product)), 201 if created else 200
    except ValueError as error:
        db.session.rollback()
        return jsonify(message=str(error)), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify(message='Datos en conflicto: revisa el slug y la categoría.'), 409
