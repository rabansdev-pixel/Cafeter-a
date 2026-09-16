from flask import Blueprint, abort, jsonify, render_template, request
from app.services.menu_service import MenuError, MenuService

cafe_bp = Blueprint("cafe", __name__)


@cafe_bp.app_context_processor
def shared_content():
    return {"cafe": MenuService.content(), "menu_categories": MenuService.categories()}


@cafe_bp.route("/menu")
def menu():
    return render_template("pages/menu.html", categories=MenuService.categories())


@cafe_bp.route("/producto/<slug>")
def product(slug):
    item = MenuService.get(slug)
    if not item:
        abort(404)
    return render_template("pages/menu_product.html", item=item)


@cafe_bp.route("/carrito")
def cart():
    return render_template("pages/cart.html")


@cafe_bp.route("/espacio")
def space():
    return render_template("pages/space.html")


@cafe_bp.route("/experiencia")
def experience():
    return render_template("pages/experience.html")


@cafe_bp.route("/visitanos")
def visit():
    return render_template("pages/visit.html")


@cafe_bp.route("/api/menu")
def menu_data():
    response = jsonify(products=MenuService.products())
    response.headers["Cache-Control"] = "no-store"
    return response


@cafe_bp.route("/api/order/quote", methods=["POST"])
def quote():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(message="No pudimos leer tu selección."), 400
    try:
        response = jsonify(MenuService.quote(data.get("items")))
        response.headers["Cache-Control"] = "no-store"
        return response
    except MenuError as error:
        return jsonify(message=str(error)), 400
