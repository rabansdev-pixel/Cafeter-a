from flask import Blueprint, jsonify, request
from app.services.menu_service import MenuService, MenuError

cart_api_bp = Blueprint("cart_api", __name__, url_prefix="/api/cart")

@cart_api_bp.route("/calculate", methods=["POST"])
def calculate_cart():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(message="Formato inválido."), 400
    try:
        return jsonify(status="success", data=MenuService.quote(data.get("items", [])))
    except MenuError as error:
        return jsonify(message=str(error)), 400
