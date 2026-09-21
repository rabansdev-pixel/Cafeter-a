from flask import Blueprint, jsonify, request
from app.services.cart_service import CartService

cart_api_bp = Blueprint("cart_api", __name__, url_prefix="/api/cart")


@cart_api_bp.route("/calculate", methods=["POST"])
def calculate_cart():
    """Recibe los ítems del carrito y calcula subtotales, envío gratis y total."""
    data = request.get_json() or {}
    items = data.get("items", [])

    if not isinstance(items, list):
        return jsonify({"status": "error", "message": "Formato de ítems inválido"}), 400

    totals = CartService.calculate_totals(items)
    return jsonify({"status": "success", "data": totals}), 200
