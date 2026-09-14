from typing import List, Dict, Any


class CartService:
    """Servicio de lógica de negocio para el carrito de compras de la cafetería."""

    FREE_SHIPPING_THRESHOLD = 50000.0  # $50.000 COP
    STANDARD_SHIPPING_COST = 8500.0  # $8.500 COP
    TAX_RATE = 0.0  # Café tostado suele estar exento o tasa preferencial

    @classmethod
    def calculate_totals(cls, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula subtotales, costo de envío, descuentos y total general.
        Cada item debe tener: {'id': int, 'name': str, 'price': float, 'quantity': int}
        """
        if not items:
            return {
                "items_count": 0,
                "subtotal": 0.0,
                "shipping": 0.0,
                "is_free_shipping": False,
                "free_shipping_remaining": cls.FREE_SHIPPING_THRESHOLD,
                "total": 0.0,
                "formatted_subtotal": "$0",
                "formatted_shipping": "$0",
                "formatted_total": "$0",
            }

        subtotal = 0.0
        total_quantity = 0

        for item in items:
            quantity = max(1, int(item.get("quantity", 1)))
            price = max(0.0, float(item.get("price", 0.0)))
            subtotal += price * quantity
            total_quantity += quantity

        is_free_shipping = subtotal >= cls.FREE_SHIPPING_THRESHOLD
        shipping = 0.0 if is_free_shipping else cls.STANDARD_SHIPPING_COST
        remaining_for_free_shipping = max(0.0, cls.FREE_SHIPPING_THRESHOLD - subtotal)
        total = subtotal + shipping

        return {
            "items_count": total_quantity,
            "subtotal": subtotal,
            "shipping": shipping,
            "is_free_shipping": is_free_shipping,
            "free_shipping_remaining": remaining_for_free_shipping,
            "total": total,
            "formatted_subtotal": f"${subtotal:,.0f}".replace(",", "."),
            "formatted_shipping": (
                "Gratis" if is_free_shipping else f"${shipping:,.0f}".replace(",", ".")
            ),
            "formatted_total": f"${total:,.0f}".replace(",", "."),
        }
