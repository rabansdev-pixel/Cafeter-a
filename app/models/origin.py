from app.core.extensions import db


class Origin(db.Model):
    """Modelo de origen y terroir del grano de café."""

    __tablename__ = "origins"

    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(80), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    farm = db.Column(db.String(120), nullable=True)
    altitude_meters = db.Column(db.Integer, nullable=False, default=1800)
    process = db.Column(
        db.String(60), nullable=False, default="Lavado"
    )  # Lavado, Honey, Natural, Anaeróbico
    variety = db.Column(
        db.String(80), nullable=True, default="Arábica"
    )  # Geisha, Borbón, Caturra, Castillo

    products = db.relationship("Product", backref="origin", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "country": self.country,
            "region": self.region,
            "farm": self.farm,
            "altitude": f"{self.altitude_meters} msnm",
            "process": self.process,
            "variety": self.variety,
        }
