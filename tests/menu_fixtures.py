"""Artificial records for tests only. Never imported by the application."""

from copy import deepcopy
from app.cafe_content import CAFE


def confirmed_menu():
    content = deepcopy(CAFE)
    content.update(
        menu_is_example=False,
        currency="USD",
        menu=[
            {
                "name": "Categoría de prueba",
                "items": [
                    {
                        "id": "test-simple",
                        "slug": "seleccion-de-prueba",
                        "name": "Selección de prueba",
                        "published": True,
                        "availability": "available",
                        "price": "3.25",
                        "description": "Registro artificial para verificar el flujo.",
                        "featured": True,
                    },
                    {
                        "id": "test-custom",
                        "slug": "seleccion-personalizable",
                        "name": "Selección personalizable",
                        "published": True,
                        "availability": "available",
                        "price": "4.00",
                        "short_description": "Registro artificial con opciones y complementos.",
                        "long_description": "Solo se utiliza en pruebas; no representa la oferta del café.",
                        "options": [
                            {
                                "id": "size",
                                "label": "Tamaño de prueba",
                                "required": True,
                                "choices": [
                                    {
                                        "id": "small",
                                        "label": "Pequeño",
                                        "price_delta": "0",
                                    },
                                    {
                                        "id": "large",
                                        "label": "Grande",
                                        "price_delta": "1.25",
                                    },
                                ],
                            }
                        ],
                        "modifiers": [
                            {
                                "id": "extra",
                                "label": "Complemento de prueba",
                                "max_choices": 1,
                                "choices": [
                                    {
                                        "id": "extra-a",
                                        "label": "Complemento A",
                                        "price_delta": ".50",
                                    },
                                    {
                                        "id": "extra-b",
                                        "label": "Complemento B",
                                        "price_delta": ".75",
                                    },
                                ],
                            }
                        ],
                    },
                ],
            },
            {
                "name": "Otra categoría",
                "items": [
                    {
                        "id": "test-unavailable",
                        "slug": "seleccion-no-disponible",
                        "name": "Selección no disponible",
                        "published": True,
                        "availability": "unavailable",
                        "price": "5.00",
                    },
                    {
                        "id": "test-unpriced",
                        "slug": "seleccion-sin-precio",
                        "name": "Selección sin precio",
                        "published": True,
                        "availability": "available",
                        "price": None,
                    },
                    {
                        "id": "test-hidden",
                        "slug": "seleccion-oculta",
                        "name": "No publicar",
                        "published": False,
                        "availability": "available",
                        "price": "10.00",
                    },
                ],
            },
        ],
    )
    return content
