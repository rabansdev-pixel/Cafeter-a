"""Product validation and mutations shared by HTML administration and JSON API."""
from decimal import Decimal
import re
from app.core.extensions import db
from app.models import Product, Category
from app.services.auth_service import audit
from app.services.menu_service import cents, media_url


def product_data(product):
    return dict(id=product.id, name=product.name, slug=product.slug,
                description=product.description, price=str(product.price),
                category=product.category, category_id=product.category_id,
                image=product.image, stock=product.stock, active=product.is_active,
                created_at=product.created_at.isoformat() if product.created_at else None,
                updated_at=product.updated_at.isoformat() if product.updated_at else None)


def save_product(data, product=None):
    if not isinstance(data, dict):
        raise ValueError('Datos inválidos.')
    allowed = {'name', 'slug', 'description', 'price', 'category_id', 'image', 'stock', 'active', 'tagline'}
    if set(data) - allowed:
        raise ValueError('Hay campos no permitidos.')
    previous = product_data(product) if product else {}
    values = dict(previous, tagline=product.tagline if product else '')
    values.update(data)
    name = values.get('name', '')
    slug = values.get('slug', '')
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 120:
        raise ValueError('Nombre obligatorio, máximo 120 caracteres.')
    if not isinstance(slug, str) or len(slug) > 140 or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        raise ValueError('Usa un slug de letras minúsculas, números y guiones.')
    price = Decimal(cents(values.get('price'))) / 100
    try:
        if isinstance(values.get('category_id'), (bool, float)):
            raise ValueError()
        category_id = int(values.get('category_id'))
    except (TypeError, ValueError):
        raise ValueError('Elige una categoría válida.') from None
    if not db.session.get(Category, category_id):
        raise ValueError('La categoría no existe.')
    stock = values.get('stock')
    if stock == '':
        stock = None
    if stock is not None:
        if isinstance(stock, bool) or not re.fullmatch(r'\d+', str(stock)) or int(stock) > 2147483647:
            raise ValueError('Stock debe ser un entero no negativo o quedar vacío.')
        stock = int(stock)
    image = media_url(values.get('image'))
    if not image or len(image) > 255:
        raise ValueError('La imagen debe ser una ruta local o URL HTTPS (máximo 255 caracteres).')
    active = values.get('active', True)
    if type(active) is not bool:
        raise ValueError('active debe ser verdadero o falso.')
    description, tagline = values.get('description', ''), values.get('tagline', '')
    if not isinstance(description, str) or len(description) > 10000 or not isinstance(tagline, str) or len(tagline) > 200:
        raise ValueError('Descripción demasiado larga.')
    is_new = product is None
    if is_new:
        product = Product(menu_id='zd-' + slug, weight_grams=0, details={})
        db.session.add(product)
    product.name, product.slug, product.price = name.strip(), slug, price
    product.description, product.tagline = description, tagline
    product.category_id, product.image_url = category_id, image
    product.stock, product.is_active = stock, active
    if previous and previous['image'] != image:
        product.details = dict(product.details or {}, image_small=image)
    db.session.flush()
    audit('product.create' if is_new else 'product.update', 'product', product.id,
          {'before': previous, 'after': product_data(product)})
    db.session.commit()
    return product


def deactivate_product(product):
    before = product.is_active
    product.is_active = False
    audit('product.deactivate', 'product', product.id, {'active_before': before, 'active_after': False})
    db.session.commit()
