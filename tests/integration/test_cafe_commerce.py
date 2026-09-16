import pytest
from tests.menu_fixtures import confirmed_menu
from app.services.menu_service import MenuService, MenuError, cents


@pytest.fixture
def menu_data(app, monkeypatch):
    content = confirmed_menu()
    monkeypatch.setitem(app.config, "CAFE_CONTENT", content)
    return content


@pytest.mark.parametrize(
    "path", ["/menu", "/catalogo", "/espacio", "/experiencia", "/visitanos", "/carrito"]
)
def test_new_routes_support_direct_requests(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert b"ZERO DAY" in response.data
    assert b'aria-current="page"' in response.data or path == "/catalogo"


def test_unverified_seed_and_example_content_never_becomes_menu(client):
    response = client.get("/api/menu")
    assert response.json == {"products": []}
    assert client.get("/producto/geisha-huila-reserva-privada").status_code == 404
    for path in ["/menu", "/visitanos", "/"]:
        body = client.get(path).get_data(as_text=True)
        assert "https://www.instagram.com/" not in body
        assert "Cold brew" not in body
        assert "68,000" not in body


def test_menu_uses_confirmed_content_and_exposes_valid_detail(client, menu_data):
    assert len(client.get("/api/menu").json["products"]) == 4
    page = client.get("/menu").get_data(as_text=True)
    assert "3.25 USD" in page
    assert 'data-quick-add="test-simple"' in page
    assert 'data-quick-add="test-custom"' not in page
    assert "/producto/seleccion-personalizable" in page
    assert "No publicar" not in page
    detail = client.get("/producto/seleccion-personalizable").get_data(as_text=True)
    assert "product-order" in detail and "Tamaño de prueba" in detail
    for slug in ["seleccion-no-disponible", "seleccion-sin-precio"]:
        detail = client.get("/producto/" + slug).get_data(as_text=True)
        assert "data-add-button" not in detail
        assert "no está disponible para pedidos" in detail
    assert client.get("/producto/seleccion-oculta").status_code == 404


def test_authoritative_quote_ignores_client_prices(client, menu_data, csrf_headers):
    response = client.post(
        "/api/order/quote",
        headers=csrf_headers,
        json={
            "items": [
                {
                    "product_id": "test-custom",
                    "quantity": 2,
                    "price": 0.01,
                    "options": {"size": "large"},
                    "modifiers": {"extra": ["extra-a"]},
                }
            ]
        },
    )
    assert response.status_code == 200
    result = response.json
    assert result["subtotal_cents"] == 1150
    assert result["lines"][0]["unit_cents"] == 575
    assert result["formatted_subtotal"] == "11.50 USD"
    assert result["quantity"] == 2
    assert result["checkout_available"] is False
    assert "shipping" not in result and "tax" not in result


@pytest.mark.parametrize(
    "line",
    [
        {"product_id": "test-simple", "quantity": 0},
        {"product_id": "test-simple", "quantity": 100},
        {"product_id": "test-simple", "quantity": True},
        {"product_id": "test-simple", "quantity": 1.5},
        {"product_id": ["test-simple"], "quantity": 1},
    ],
)
def test_quote_rejects_invalid_quantities_and_ids(
    client, menu_data, csrf_headers, line
):
    assert (
        client.post(
            "/api/order/quote", json={"items": [line]}, headers=csrf_headers
        ).status_code
        == 400
    )


@pytest.mark.parametrize(
    "selection",
    [
        {"options": {}},
        {"options": {"size": "unknown"}},
        {"options": {"size": ["large"]}},
        {"options": {"size": "large", "invented": "anything"}},
        {"options": {"size": "large"}, "modifiers": {"extra": ["extra-a", "extra-b"]}},
        {"options": {"size": "large"}, "modifiers": {"extra": ["extra-a", "extra-a"]}},
        {"options": {"size": "large"}, "modifiers": {"extra": ["unknown"]}},
    ],
)
def test_invalid_customization_is_not_in_subtotal(
    client, menu_data, csrf_headers, selection
):
    result = client.post(
        "/api/order/quote",
        headers=csrf_headers,
        json={"items": [{"product_id": "test-custom", "quantity": 1, **selection}]},
    ).json
    assert result["has_errors"] and result["subtotal_cents"] == 0
    assert result["lines"][0]["available"] is False


def test_stale_and_unpriced_lines_can_be_removed_without_being_charged(
    client, menu_data, csrf_headers
):
    result = client.post(
        "/api/order/quote",
        headers=csrf_headers,
        json={
            "items": [
                {"product_id": key, "quantity": 1}
                for key in [
                    "test-simple",
                    "removed",
                    "test-unavailable",
                    "test-unpriced",
                ]
            ]
        },
    ).json
    assert len(result["lines"]) == 4
    assert result["subtotal_cents"] == 325
    assert result["has_errors"] is True
    menu_data["menu"][0]["items"][0]["price"] = "4.00"
    updated = client.post(
        "/api/order/quote",
        headers=csrf_headers,
        json={"items": [{"product_id": "test-simple", "quantity": 1}]},
    ).json
    assert updated["subtotal_cents"] == 400


def test_quote_failure_states_and_csrf(client, menu_data, csrf_headers):
    assert client.post("/api/order/quote", json={"items": []}).status_code == 400
    for body in [[], None, {"items": {}}, {"items": [{}] * 51}]:
        assert (
            client.post("/api/order/quote", json=body, headers=csrf_headers).status_code
            == 400
        )
    empty = client.post("/api/order/quote", json={"items": []}, headers=csrf_headers)
    assert empty.status_code == 200 and empty.json["subtotal_cents"] == 0
    assert empty.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize(
    "value", [None, True, "-1", "NaN", "Infinity", "0.001", "1000000000"]
)
def test_money_rejects_invalid_amounts(value):
    with pytest.raises(MenuError):
        cents(value)


def test_currency_must_be_confirmed(app, menu_data):
    menu_data["currency"] = None
    with app.app_context():
        assert not any(p["orderable"] for p in MenuService.products())
