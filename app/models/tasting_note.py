from app.core.extensions import db


class TastingProfile(db.Model):
    """
    Modelo para el perfil de cata, notas sensoriales y niveles en escala del 1 al 10.
    """

    __tablename__ = "tasting_profiles"

    id = db.Column(db.Integer, primary_key=True)
    roast_level = db.Column(
        db.String(40), nullable=False, default="Medio"
    )  # Claro, Medio, Oscuro
    acidity = db.Column(db.Integer, nullable=False, default=7)  # 1 a 10
    body = db.Column(db.Integer, nullable=False, default=6)  # 1 a 10
    sweetness = db.Column(db.Integer, nullable=False, default=8)  # 1 a 10
    aroma = db.Column(db.Integer, nullable=False, default=9)  # 1 a 10
    flavor_notes = db.Column(
        db.String(255), nullable=False
    )  # Ej: "Jazmín, Bergamota, Miel silvestre"

    product = db.relationship(
        "Product", backref="tasting_profile", uselist=False, lazy=True
    )

    def notes_list(self):
        """Retorna las notas como lista de strings limpios."""
        return [note.strip() for note in self.flavor_notes.split(",") if note.strip()]

    def to_radar_dict(self):
        """Formato listo para el componente visual de radar en el frontend."""
        return {
            "roast_level": self.roast_level,
            "acidity": self.acidity,
            "body": self.body,
            "sweetness": self.sweetness,
            "aroma": self.aroma,
            "notes": self.notes_list(),
        }
