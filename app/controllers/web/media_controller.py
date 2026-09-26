import re
from io import BytesIO
from flask import Blueprint, abort, send_file
from app.core.extensions import db
from app.models.product_image import ProductImage

media_bp = Blueprint('media', __name__)


@media_bp.get('/media/products/<image_id>.webp')
def product_image(image_id):
    if not re.fullmatch(r'[a-f0-9]{32}', image_id):
        abort(404)
    photo = db.get_or_404(ProductImage, image_id)
    return send_file(BytesIO(photo.data), mimetype='image/webp',
                     download_name=f'{image_id}.webp', conditional=True,
                     etag=image_id, max_age=31536000)
