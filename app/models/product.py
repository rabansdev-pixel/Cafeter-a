from datetime import datetime, timezone
from app.core.extensions import db


class Product(db.Model):
    """Modelo principal de producto de café de especialidad."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(140), unique=True, nullable=False, index=True)
    tagline = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=25)
    weight_grams = db.Column(
        db.Integer, nullable=False, default=340
    )  # Bolsa de 340g / 12oz
    image_url = db.Column(db.String(255), nullable=False)

    is_featured = db.Column(db.Boolean, default=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relaciones de clave foránea
    origin_id = db.Column(db.Integer, db.ForeignKey("origins.id"), nullable=False)
    tasting_profile_id = db.Column(
        db.Integer, db.ForeignKey("tasting_profiles.id"), nullable=False
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "tagline": self.tagline,
            "description": self.description,
            "price": self.price,
            "formatted_price": f"${self.price:,.0f}".replace(",", "."),
            "stock": self.stock,
            "weight_grams": self.weight_grams,
            "image_url": self.image_url,
            "is_featured": self.is_featured,
            "origin": self.origin.to_dict() if self.origin else None,
            "tasting": (
                self.tasting_profile.to_radar_dict() if self.tasting_profile else None
            ),
        }
