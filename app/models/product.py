from datetime import datetime, timezone
from app.core.extensions import db


class Product(db.Model):
    """Modelo principal de producto de café de especialidad."""

    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(140), unique=True, nullable=False, index=True)
    tagline = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=True)
    weight_grams = db.Column(
        db.Integer, nullable=False, default=340
    )  # Bolsa de 340g / 12oz
    image_url = db.Column(db.String(255), nullable=False)

    is_featured = db.Column(db.Boolean, default=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relaciones de clave foránea
    origin_id = db.Column(db.Integer, db.ForeignKey("origenes.id"), nullable=True)
    tasting_profile_id = db.Column(
        db.Integer, db.ForeignKey("perfiles_cata.id"), nullable=True
    )

    category_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), index=True)
    category_record = db.relationship("Category")
    menu_id = db.Column(db.String(160), unique=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    details = db.Column(db.JSON, nullable=False, default=dict)
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        db.CheckConstraint("price >= 0", name="products_price_nonnegative"),
        db.CheckConstraint("stock IS NULL OR stock >= 0", name="products_stock_nonnegative"),
    )

    @property
    def category(self):
        return self.category_record.name if self.category_record else None

    @property
    def image(self):
        return self.display_image_url

    @property
    def active(self):
        return self.is_active

    def menu_data(self):
        return dict(self.details or {}, id=self.menu_id, slug=self.slug, name=self.name,
                    price=str(self.price), published=self.is_active,
                    short_description=self.tagline, long_description=self.description,
                    image=self.image, featured=self.is_featured, stock=self.stock,
                    availability="unavailable" if self.stock == 0 else (self.details or {}).get("availability", "available"))

    @property
    def display_image_url(self):
        """Resolve legacy illustration URLs without changing stored records."""
        known = ('geisha-huila', 'yirgacheffe', 'borbon-rosado', 'kenia-nyeri')
        for name in known:
            if self.image_url == f"/static/img/products/{name}.svg":
                return f"/static/img/products/{name}.webp"
        return self.image_url

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
            "image_url": self.display_image_url,
            "is_featured": self.is_featured,
            "origin": self.origin.to_dict() if self.origin else None,
            "tasting": (
                self.tasting_profile.to_radar_dict() if self.tasting_profile else None
            ),
        }
