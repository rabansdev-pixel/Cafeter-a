from flask import Blueprint, render_template
from app.services.product_service import ProductService
from app.cafe_content import CAFE, OBJECTS

main_bp = Blueprint("main", __name__)
product_service = ProductService()


@main_bp.route("/")
def home():
    """Physical café: editorial content, original objects and verified visit details."""
    return render_template("pages/home.html", cafe=CAFE, objects=OBJECTS)



@main_bp.route("/origenes")
def origins():
    """Página de historia de fincas, altitud y procesos de fermentación."""
    products = product_service.get_catalog()
    return render_template("pages/origins.html", products=products)


@main_bp.route("/metodos")
def methods():
    """Guía interactiva de métodos de extracción de café de especialidad."""
    return render_template("pages/methods.html")
