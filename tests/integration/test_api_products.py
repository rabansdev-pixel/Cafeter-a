def test_api_health_check(client):
    """Verifica el endpoint de healthcheck para Docker."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "cafeteria-especialidad"


def test_api_get_products_list(client):
    """Verifica el listado completo de productos en formato JSON."""
    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["count"] >= 4
    assert len(data["data"]) >= 4


def test_api_get_products_filter_by_roast(client):
    """Verifica el filtrado de productos por query parameter roast."""
    response = client.get("/api/products?roast=Claro")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    for item in data["data"]:
        assert "Claro" in item["tasting_profile"]["roast_level"]


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


def test_api_calculate_cart_totals(client, csrf_headers):
    """Verifica el cálculo del carrito a través del API REST."""
    payload = {
        "items": [{"id": 1, "name": "Geisha Huila", "price": 68000.0, "quantity": 1}]
    }
    response = client.post("/api/cart/calculate", json=payload, headers=csrf_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["data"]["subtotal"] == 68000.0
    assert data["data"]["is_free_shipping"] is True


def test_api_calculate_cart_invalid_payload(client, csrf_headers):
    """Verifica manejo de errores ante datos malformados."""
    payload = {"items": "no-es-una-lista"}
    response = client.post("/api/cart/calculate", json=payload, headers=csrf_headers)
    assert response.status_code == 400
    assert response.get_json()["message"] == "Formato de ítems inválido"


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


def test_country_filter_sanitizes_html_and_escapes_wildcards(client):
    response = client.get(
        "/api/products", query_string={"country": " <b>Colombia</b> ", "roast": "Claro"}
    )
    # nh3 conserva etiquetas permitidas; no deben ampliar la consulta SQL.
    assert response.get_json()["count"] == 0
    response = client.get(
        "/api/products", query_string={"country": " Colombia ", "roast": "Claro"}
    )
    products = response.get_json()["data"]
    assert products
    assert all(p["origin"]["country"] == "Colombia" for p in products)
    for country in ["%", "_", "' OR 1=1 --"]:
        response = client.get("/api/products", query_string={"country": country})
        assert response.status_code == 200
        assert response.get_json()["count"] == 0
