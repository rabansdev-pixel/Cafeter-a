from flask import Blueprint, render_template
from app.services.product_service import ProductService

main_bp = Blueprint("main", __name__)
product_service = ProductService()


@main_bp.route("/")
def home():
    """Página de inicio con Hero inmersivo y Bento Grid centrado en el café."""
    hero_product = product_service.get_hero_product()
    featured_products = product_service.get_featured_showcase()
    all_products = product_service.get_catalog()
    return render_template(
        "pages/home.html",
        hero_product=hero_product,
        featured_products=featured_products,
        all_products=all_products,
    )


@main_bp.route("/origenes")
def origins():
    """Página de historia de fincas, altitud y procesos de fermentación."""
    products = product_service.get_catalog()
    return render_template("pages/origins.html", products=products)


@main_bp.route("/metodos")
def methods():
    """Guía interactiva de métodos de extracción de café de especialidad."""
    return render_template("pages/methods.html")
