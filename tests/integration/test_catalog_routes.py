def test_home_page_renders_successfully(client):
    """Verifica que la página principal cargue con status 200 y contenga la marca."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"ZERO-DAY" in response.data
    assert b"Geisha" in response.data
    assert b"radar" in response.data.lower()


def test_catalog_page_renders_successfully(client):
    """Verifica la carga del catálogo y la presencia de productos."""
    response = client.get("/catalogo")
    assert response.status_code == 200
    assert b"Nuestra Cava de Caf" in response.data


def test_origins_page_renders(client):
    """Verifica la carga de la página de terroirs y orígenes."""
    response = client.get("/origenes")
    assert response.status_code == 200
    assert b"San Agust" in response.data


def test_methods_page_renders(client):
    """Verifica la página de guía de métodos de preparación."""
    response = client.get("/metodos")
    assert response.status_code == 200
    assert b"Hario V60" in response.data


def test_product_detail_page_valid_slug(client):
    """Verifica la ficha técnica de un café existente."""
    response = client.get("/cafe/geisha-huila-reserva-privada")
    assert response.status_code == 200
    assert b"Geisha Huila Reserva Privada" in response.data
    assert b"1950 msnm" in response.data


def test_product_detail_page_invalid_slug_returns_404(client):
    """Verifica que un slug inexistente responda 404."""
    response = client.get("/cafe/grano-inexistente-xyz")
    assert response.status_code == 404
    assert b"404" in response.data
