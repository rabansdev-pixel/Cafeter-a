from app.services.cart_service import CartService


def test_calculate_totals_empty_cart():
    """Verifica el cálculo para un carrito vacío."""
    result = CartService.calculate_totals([])
    assert result["items_count"] == 0
    assert result["subtotal"] == 0.0
    assert result["shipping"] == 0.0
    assert result["total"] == 0.0
    assert result["is_free_shipping"] is False


def test_calculate_totals_below_threshold():
    """Verifica que compras menores a $50.000 apliquen costo de envío."""
    items = [{"id": 1, "name": "Bolsa de Prueba", "price": 35000.0, "quantity": 1}]
    result = CartService.calculate_totals(items)
    assert result["items_count"] == 1
    assert result["subtotal"] == 35000.0
    assert result["shipping"] == 8500.0
    assert result["total"] == 43500.0
    assert result["is_free_shipping"] is False
    assert result["free_shipping_remaining"] == 15000.0


def test_calculate_totals_above_threshold():
    """Verifica que compras iguales o mayores a $50.000 tengan envío gratis."""
    items = [{"id": 1, "name": "Geisha Huila", "price": 68000.0, "quantity": 1}]
    result = CartService.calculate_totals(items)
    assert result["items_count"] == 1
    assert result["subtotal"] == 68000.0
    assert result["shipping"] == 0.0
    assert result["total"] == 68000.0
    assert result["is_free_shipping"] is True
    assert result["free_shipping_remaining"] == 0.0


def test_calculate_totals_multiple_items():
    """Verifica suma de múltiples cantidades y artículos."""
    items = [
        {"id": 1, "name": "Café A", "price": 20000.0, "quantity": 2},  # 40.000
        {
            "id": 2,
            "name": "Café B",
            "price": 30000.0,
            "quantity": 1,
        },  # 30.000 -> Total 70.000
    ]
    result = CartService.calculate_totals(items)
    assert result["items_count"] == 3
    assert result["subtotal"] == 70000.0
    assert result["is_free_shipping"] is True
    assert result["total"] == 70000.0
