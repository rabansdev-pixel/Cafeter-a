def test_home_page_renders_successfully(client):
    """Verifica que la página principal cargue con status 200 y contenga la marca."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"ZERO-DAY" in response.data
    assert b'Ayacucho y 8va Norte' in response.data
    assert b'8:00 a. m.' in response.data
    assert response.data.count(b'class="site-nav"') == 1
    assert b'/static/img/products/hero-v1-web.mp4' in response.data
    assert b'/static/img/products/coffe.mp4' in response.data
    assert b' muted loop playsinline' in response.data
    assert b'js-add-to-cart' not in response.data
    assert b'cart-drawer' not in response.data
    for anchor in ['cafe', 'espacio', 'menu', 'seleccion', 'visitanos']:
        assert f'id="{anchor}"'.encode() in response.data


def test_catalog_page_renders_successfully(client):
    """Verifica la carga del catálogo y la presencia de productos."""
    response = client.get("/catalogo")
    assert response.status_code == 200
    assert b"Costa Coffee" in response.data
    assert b"data-model" in response.data
    assert b"data-quick-add" not in response.data
    assert b"js-add-to-cart" not in response.data
    assert b"data-price" not in response.data


def test_origins_page_renders(client):
    """Verifica la carga de la página de terroirs y orígenes."""
    response = client.get("/origenes")
    assert response.status_code == 301
    assert response.headers["Location"] == "/catalogo#origen"
    assert b'id="origen"' in client.get("/catalogo").data


def test_methods_page_renders(client):
    """Verifica la página de guía de métodos de preparación."""
    response = client.get("/metodos")
    assert response.status_code == 301
    assert response.headers["Location"] == "/experiencia#metodos"
    assert b"Hario V60" in client.get("/experiencia").data


def test_product_detail_page_valid_slug(client):
    """Verifica la ficha técnica de un café existente."""
    response = client.get("/cafe/geisha-huila-reserva-privada")
    assert response.status_code == 301
    assert response.headers["Location"] == "/catalogo#origen"
    assert client.get(response.headers["Location"]).status_code == 200


def test_product_detail_page_invalid_slug_returns_404(client):
    """Verifica que un slug inexistente responda 404."""
    response = client.get("/cafe/grano-inexistente-xyz")
    assert response.status_code == 404
    assert b"404" in response.data
