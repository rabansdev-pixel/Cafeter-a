import pytest
from app.core.extensions import db
from app.models import Product, Category
from app.services.product_service import ProductService


@pytest.fixture
def store_product(app):
    with app.app_context():
        category = Category(name="API test")
        db.session.add(category)
        db.session.flush()
        product = Product(category_id=category.id, name="Café de prueba", slug="cafe-api-test", menu_id="api-test",
                          tagline="", description="", price=3.25, stock=10,
                          image_url="/static/test.webp", details={"availability": "available"})
        db.session.add(product)
        db.session.commit()
        yield product
        db.session.delete(product)
        db.session.flush()
        db.session.delete(category)
        db.session.commit()


def test_api_health_check(client):
    """Verifica el endpoint de healthcheck para Docker."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "cafeteria-especialidad"


def test_api_get_products_list(client, store_product):
    """Verifica el listado completo de productos en formato JSON."""
    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["count"] == 1
    assert data["data"][0]["slug"] == "cafe-api-test"


def test_catalog_filters_by_roast(app):
    with app.app_context():
        products = ProductService().get_catalog(roast="Claro")
        assert products
        assert all("Claro" in p.tasting_profile.roast_level for p in products)


def test_api_get_radar_metrics(client):
    """Verifica la respuesta del endpoint de radar para un producto válido."""
    response = client.get("/api/products/1/radar")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "radar" in data["data"]
    assert "acidity" in data["data"]["radar"]


def test_api_get_radar_metrics_not_found(client):
    """Verifica error 404 para ID inexistente."""
    response = client.get("/api/products/9999/radar")
    assert response.status_code == 404
    data = response.get_json()
    assert data["status"] == "error"


def test_api_calculate_cart_totals(client, csrf_headers, store_product):
    """Verifica el cálculo del carrito a través del API REST."""
    payload = {
        "items": [
            {"product_id": "api-test", "price": 0.01, "quantity": 2}
        ]
    }
    response = client.post(
        "/api/cart/calculate", json=payload, headers=csrf_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["data"]["subtotal_cents"] == 650
    assert data["data"]["has_errors"] is False


def test_api_calculate_cart_invalid_payload(client, csrf_headers):
    """Verifica manejo de errores ante datos malformados."""
    payload = {"items": "no-es-una-lista"}
    response = client.post(
        "/api/cart/calculate", json=payload, headers=csrf_headers
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "El carrito admite hasta 50 selecciones."


def test_api_get_product_by_slug_valid(client):
    """Verifica consulta de producto por slug vía API."""
    response = client.get("/api/products/geisha-huila-reserva-privada")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["data"]["name"] == "Geisha Huila Reserva Privada"


def test_api_get_product_by_slug_invalid(client):
    """Verifica 404 al consultar un slug inexistente vía API."""
    response = client.get("/api/products/slug-inexistente-123")
    assert response.status_code == 404
    data = response.get_json()
    assert data["status"] == "error"


def test_country_filter_escapes_wildcards(app):
    with app.app_context():
        service = ProductService()
        products = service.get_catalog(country=" Colombia ", roast="Claro")
        assert products
        assert all(p.origin.country == "Colombia" for p in products)
        for country in ["<b>Colombia</b>", "%", "_", "' OR 1=1 --"]:
            assert service.get_catalog(country=country) == []
