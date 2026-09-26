from io import BytesIO
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError
from app.core.extensions import db
from app.models.product_image import ProductImage

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 24_000_000


def store_image(upload):
    """Validate actual pixels and re-encode: no filenames, EXIF or executable content."""
    raw = upload.stream.read(MAX_UPLOAD_BYTES + 1)
    if not raw or len(raw) > MAX_UPLOAD_BYTES:
        raise ValueError('La foto debe pesar entre 1 byte y 8 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw), formats=['JPEG', 'PNG', 'WEBP']) as source:
                if source.width * source.height > MAX_PIXELS:
                    raise ValueError('La imagen supera los 24 megapíxeles.')
                if getattr(source, 'is_animated', False):
                    raise ValueError('Elige una foto estática, sin animación.')
                source.load()
                photo = ImageOps.exif_transpose(source).convert('RGB')
                photo.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
                # Copy pixels into a clean image to discard all embedded metadata.
                clean = Image.new('RGB', photo.size)
                clean.paste(photo)
                output = BytesIO()
                clean.save(output, format='WEBP', quality=90, method=4)
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('El archivo no es una imagen JPG, PNG o WebP válida.') from None
    image = ProductImage(data=output.getvalue())
    db.session.add(image)
    db.session.flush()
    return f'/media/products/{image.id}.webp'
