from pathlib import Path

import pytest

from app.models.product import Product
from app.schemas.product_schema import ProductSchema


@pytest.mark.parametrize('name', [
    'geisha-huila', 'yirgacheffe', 'borbon-rosado', 'kenia-nyeri',
])
def test_legacy_product_images_resolve_without_database_mutation(name):
    legacy = f'/static/img/products/{name}.svg'
    current = f'/static/img/products/{name}.webp'
    product = Product(name=name, price=100, image_url=legacy)
    assert product.display_image_url == current
    assert product.to_dict()['image_url'] == current
    assert ProductSchema().dump(product)['image_url'] == current
    assert product.image_url == legacy
    assert Path('app' + current).is_file()


def test_custom_product_images_are_preserved():
    product = Product(image_url='/static/img/custom-photo.webp')
    assert product.display_image_url == product.image_url
