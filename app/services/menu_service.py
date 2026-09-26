"""Confirmed café menu and authoritative quotes, independent of legacy bean seeds.

Prices in content are decimal strings; arithmetic and API amounts use integer cents.
PostgreSQL supplies products; CAFE supplies business metadata only.
"""

from decimal import Decimal, InvalidOperation
import re
from urllib.parse import urlsplit
from flask import current_app, g, has_request_context
from app.cafe_content import CAFE


class MenuError(ValueError):
    pass


def cents(value):
    if isinstance(value, bool) or value is None:
        raise MenuError("Precio no configurado.")
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0 or amount > 100000:
            raise MenuError("Precio inválido.")
        if amount != amount.quantize(Decimal(".01")):
            raise MenuError("El precio debe tener como máximo dos decimales.")
        return int(amount * 100)
    except (InvalidOperation, ValueError, TypeError) as error:
        raise MenuError("Precio inválido.") from error


def money(amount, currency):
    return (
        f"{amount / 100:,.2f} {currency}" if amount is not None and currency else None
    )


def media_url(value):
    """Allow local media or HTTPS; never javascript/data URLs from content."""
    if not value or not isinstance(value, str):
        return None
    if value.startswith("/") and not value.startswith("//"):
        return value
    if urlsplit(value).scheme == "https":
        return value
    return None


class MenuService:
    @staticmethod
    def content():
        return current_app.config.get("CAFE_CONTENT", CAFE)

    @classmethod
    def stored_categories(cls):
        if has_request_context() and hasattr(g, 'stored_menu_categories'):
            return g.stored_menu_categories
        from app.models import Category, Product
        from app.core.extensions import db
        groups = []
        categories = db.session.execute(db.select(Category).order_by(Category.position, Category.id)).scalars().all()
        products = db.session.execute(db.select(Product).where(Product.menu_id.isnot(None), Product.is_active.is_(True)).order_by(Product.position, Product.id)).scalars().all()
        for category in categories:
            groups.append(dict(name=category.name, intro=category.intro,
                               items=[p.menu_data() for p in products if p.category_id == category.id]))
        if has_request_context():
            g.stored_menu_categories = groups
        return groups

    @classmethod
    def products(cls):
        content = cls.content()
        if content.get("menu_is_example", True):
            return []
        currency = content.get("currency")
        if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
            currency = None
        result, ids, slugs = [], set(), set()
        for category in cls.stored_categories():
            for raw in category.get("items", []):
                if raw.get("published") is not True:
                    continue
                item = dict(raw)
                if not all(
                    isinstance(item.get(k), str) and item[k].strip()
                    for k in ("id", "slug", "name")
                ):
                    continue
                if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item["slug"]):
                    continue
                if item["id"] in ids or item["slug"] in slugs:
                    continue
                ids.add(item["id"])
                slugs.add(item["slug"])
                try:
                    price = cents(item.get("price"))
                except MenuError:
                    price = None
                item.update(
                    category=category["name"],
                    price_cents=price,
                    currency=currency,
                    formatted_price=money(price, currency),
                    short_description=item.get(
                        "short_description", item.get("description", "")
                    ),
                    long_description=item.get("long_description", ""),
                    image=media_url(item.get("image")),
                    image_small=media_url(item.get("image_small")),
                    gallery=item.get("gallery", []),
                    options=item.get("options", []),
                    modifiers=item.get("modifiers", []),
                    featured=item.get("featured", False),
                )
                # Unconfirmed availability and missing prices never become a free purchase.
                item["orderable"] = (
                    item.get("availability") == "available"
                    and price is not None
                    and bool(currency)
                )
                item["customizable"] = bool(item["options"] or item["modifiers"])
                result.append(item)
        return result

    @classmethod
    def categories(cls):
        categories = []
        for item in cls.products():
            group = next(
                (group for group in categories if group["name"] == item["category"]),
                None,
            )
            if group is None:
                group = dict(
                    name=item["category"],
                    anchor=f"categoria-{len(categories) + 1}",
                    intro=next((c.get("intro", "") for c in cls.stored_categories()
                                if c.get("name") == item["category"]), ""),
                    items=[],
                )
                categories.append(group)
            group["items"].append(item)
        return categories

    @classmethod
    def get(cls, slug):
        return next((p for p in cls.products() if p["slug"] == slug), None)

    @classmethod
    def quote(cls, lines):
        if not isinstance(lines, list) or len(lines) > 50:
            raise MenuError("El carrito admite hasta 50 selecciones.")
        products = {p["id"]: p for p in cls.products()}
        output, subtotal, count, has_errors = [], 0, 0, False
        requested = {}
        for line in lines:
            if isinstance(line, dict) and isinstance(line.get("product_id"), str) and type(line.get("quantity")) is int:
                key = line["product_id"]
                requested[key] = requested.get(key, 0) + line["quantity"]
        for line in lines:
            if not isinstance(line, dict) or not isinstance(
                line.get("product_id"), str
            ):
                raise MenuError("Selección inválida.")
            quantity = line.get("quantity")
            if type(quantity) is not int or not 1 <= quantity <= 99:
                raise MenuError("Elige una cantidad entre 1 y 99.")
            item = products.get(line["product_id"])
            row = {
                "product_id": line["product_id"],
                "quantity": quantity,
                "name": item["name"] if item else "Selección no disponible",
                "slug": item["slug"] if item else None,
                "image": item["image"] if item else None,
                "options": {},
                "modifiers": {},
                "selection_labels": [],
            }
            try:
                if not item or not item["orderable"]:
                    raise MenuError("Esta selección no está disponible para pedidos.")
                if item.get("stock") is not None and requested[item["id"]] > item["stock"]:
                    raise MenuError("La cantidad supera las existencias disponibles.")
                total = item["price_cents"]
                for kind in ("options", "modifiers"):
                    selected = line.get(kind, {})
                    if not isinstance(selected, dict):
                        raise MenuError("Revisa las opciones de tu selección.")
                    groups = {g["id"]: g for g in item[kind]}
                    if any(key not in groups for key in selected):
                        raise MenuError(
                            "Una opción ya no está disponible. Revisa tu selección."
                        )
                    for group_id, group in groups.items():
                        raw = selected.get(group_id, None if kind == "options" else [])
                        if kind == "options":
                            if raw is not None and not isinstance(raw, str):
                                raise MenuError("Opción inválida.")
                            values = [raw] if raw else []
                        else:
                            if not isinstance(raw, list) or not all(
                                isinstance(v, str) for v in raw
                            ):
                                raise MenuError("Complemento inválido.")
                            values = raw
                        if len(values) != len(set(values)) or len(values) > group.get(
                            "max_choices",
                            1 if kind == "options" else len(group["choices"]),
                        ):
                            raise MenuError("Revisa la cantidad de opciones elegidas.")
                        if group.get("required") and not values:
                            raise MenuError(f"Elige una opción para {group['label']}.")
                        choices = {c["id"]: c for c in group["choices"]}
                        for choice_id in values:
                            choice = choices.get(choice_id)
                            if not choice or choice.get("available", True) is not True:
                                raise MenuError("Una opción ya no está disponible.")
                            total += cents(choice.get("price_delta", "0"))
                            row["selection_labels"].append(
                                f"{group['label']}: {choice['label']}"
                            )
                        if values:
                            row[kind][group_id] = (
                                values[0] if kind == "options" else sorted(values)
                            )
                row.update(
                    available=True,
                    unit_cents=total,
                    total_cents=total * quantity,
                    formatted_unit=money(total, item["currency"]),
                    formatted_total=money(total * quantity, item["currency"]),
                )
                subtotal += total * quantity
                count += quantity
            except MenuError as error:
                row.update(available=False, error=str(error))
                has_errors = True
            output.append(row)
        currency = cls.content().get("currency")
        return {
            "lines": output,
            "subtotal_cents": subtotal,
            "formatted_subtotal": money(subtotal, currency),
            "quantity": count,
            "has_errors": has_errors,
            "checkout_available": False,
        }
