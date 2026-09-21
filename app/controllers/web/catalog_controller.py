from flask import Blueprint, render_template, abort, redirect, url_for
from app.services.product_service import ProductService
from app.cafe_content import OBJECTS

catalog_bp = Blueprint("catalog", __name__)
product_service = ProductService()


@catalog_bp.route("/catalogo")
def catalog():
    """Third-party objects, never orderable menu items."""
    return render_template("pages/catalog.html", objects=OBJECTS)


@catalog_bp.route("/cafe/<slug>")
def product_detail(slug):
    """Ficha inmersiva y sensorial de un café de especialidad."""
    product = product_service.get_by_slug(slug)
    if not product:
        abort(404)
    return redirect(url_for("catalog.catalog", _anchor="origen"), code=301)
