from typing import List, Optional, Dict, Any
from app.repositories.product_repository import ProductRepository
from app.models.product import Product
from app.models.origin import Origin
from app.models.tasting_note import TastingProfile
from app.core.extensions import db


class ProductService:
    """Lógica de negocio para productos, catálogo y perfiles de cata."""

    def __init__(self, product_repository: Optional[ProductRepository] = None):
        self.repo = product_repository or ProductRepository()

    def get_hero_product(self) -> Optional[Product]:
        """Obtiene el café insignia para el Hero interactivo."""
        featured = self.repo.get_featured()
        return featured[0] if featured else None

    def get_featured_showcase(self) -> List[Product]:
        """Obtiene los cafés destacados para la cuadrícula Bento."""
        return self.repo.get_featured()

    def get_catalog(
        self, roast: Optional[str] = None, country: Optional[str] = None
    ) -> List[Product]:
        """Catálogo filtrado por tueste o país de origen."""
        if roast or country:
            return self.repo.filter_products(roast=roast, country=country)
        return self.repo.get_all_active()

    def get_by_slug(self, slug: str) -> Optional[Product]:
        """Obtiene el detalle completo de un grano por su slug."""
        return self.repo.get_by_slug(slug)

    def get_radar_data(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Devuelve los datos calibrados del radar de cata para visualización SVG/Canvas.
        """
        product = self.repo.get_by_id(product_id)
        if not product or not product.tasting_profile:
            return None
        return {
            "product_name": product.name,
            "origin": product.origin.country if product.origin else "",
            "radar": product.tasting_profile.to_radar_dict(),
        }

    def seed_initial_data(self) -> None:
        """Siembra cafés de especialidad iniciales si la base de datos está vacía."""
        if Product.query.first():
            return  # Ya hay datos sembrados

        coffees = [
            {
                "name": "Geisha Huila Reserva Privada",
                "slug": "geisha-huila-reserva-privada",
                "tagline": (
                    "Elegancia floral sublime, jazmín silvestre "
                    "y acidez brillante de bergamota."
                ),
                "description": (
                    "Cultivado a 1.950 metros en las faldas volcánicas del Huila, "
                    "Colombia. Este microlote Geisha pasa por un proceso de "
                    "fermentación anaeróbica de 48 horas en cereza y secado lento "
                    "en camas africanas, desatando una complejidad floral inigualable."
                ),
                "price": 68000.0,
                "weight_grams": 340,
                "stock": 18,
                "image_url": "/static/img/products/geisha-huila.svg",
                "is_featured": True,
                "origin": {
                    "country": "Colombia",
                    "region": "San Agustín, Huila",
                    "farm": "Finca El Paraíso",
                    "altitude_meters": 1950,
                    "process": "Anaeróbico Natural",
                    "variety": "Geisha",
                },
                "tasting": {
                    "roast_level": "Claro",
                    "acidity": 9,
                    "body": 6,
                    "sweetness": 9,
                    "aroma": 10,
                    "flavor_notes": (
                        "Jazmín, Bergamota, Melocotón blanco, Miel de azahar"
                    ),
                },
            },
            {
                "name": "Etiopía Yirgacheffe Aricha",
                "slug": "etiopia-yirgacheffe-aricha",
                "tagline": (
                    "Cuna ancestral del café, notas a lavanda, "
                    "durazno maduro y té negro."
                ),
                "description": (
                    "De la mítica estación de lavado Aricha en las tierras altas de "
                    "Yirgacheffe. Un perfil sedoso, delicado y etéreo que representa "
                    "la pureza del grano africano con notas cítricas vivas "
                    "y final dulce prolongado."
                ),
                "price": 62000.0,
                "weight_grams": 340,
                "stock": 24,
                "image_url": "/static/img/products/yirgacheffe.svg",
                "is_featured": True,
                "origin": {
                    "country": "Etiopía",
                    "region": "Gedeo, Yirgacheffe",
                    "farm": "Comunidad de Pequeños Productores Aricha",
                    "altitude_meters": 2100,
                    "process": "Lavado Clásico",
                    "variety": "Heirloom",
                },
                "tasting": {
                    "roast_level": "Claro",
                    "acidity": 8,
                    "body": 5,
                    "sweetness": 8,
                    "aroma": 9,
                    "flavor_notes": (
                        "Lavanda, Durazno, Limoncillo, Té negro Earl Grey"
                    ),
                },
            },
            {
                "name": "Borbón Rosado Honey Quindío",
                "slug": "borbon-rosado-honey-quindio",
                "tagline": (
                    "Cuerpo cremoso a caramelo, frutos rojos "
                    "y acidez de mandarina confitada."
                ),
                "description": (
                    "Una mutación natural rarísima que combina los azúcares del borbón "
                    "rojo con la frescura del borbón amarillo. Beneficiado bajo "
                    "proceso Yellow Honey para potenciar su cuerpo y dulzor a panela."
                ),
                "price": 58000.0,
                "weight_grams": 340,
                "stock": 30,
                "image_url": "/static/img/products/borbon-rosado.svg",
                "is_featured": True,
                "origin": {
                    "country": "Colombia",
                    "region": "Génova, Quindío",
                    "farm": "Hacienda La Colina",
                    "altitude_meters": 1850,
                    "process": "Yellow Honey",
                    "variety": "Borbón Rosado",
                },
                "tasting": {
                    "roast_level": "Medio",
                    "acidity": 7,
                    "body": 8,
                    "sweetness": 9,
                    "aroma": 8,
                    "flavor_notes": (
                        "Mandarina, Caramelo toffee, Fresa silvestre, Panela"
                    ),
                },
            },
            {
                "name": "Kenia Nyeri Peaberry",
                "slug": "kenia-nyeri-peaberry",
                "tagline": (
                    "Intensidad punzante, grosella negra jugosa "
                    "y notas a ciruela roja."
                ),
                "description": (
                    "Los granos Peaberry (grano caracol) concentran todos "
                    "los nutrientes en una sola semilla redonda. Seleccionado a mano "
                    "en las laderas del Monte Kenia, ofrece acidez fosfórica "
                    "y un final frutal."
                ),
                "price": 65000.0,
                "weight_grams": 340,
                "stock": 15,
                "image_url": "/static/img/products/kenia-nyeri.svg",
                "is_featured": False,
                "origin": {
                    "country": "Kenia",
                    "region": "Nyeri County",
                    "farm": "Cooperativa Karindundu",
                    "altitude_meters": 1900,
                    "process": "Doble Lavado Keniano",
                    "variety": "SL28 & SL34",
                },
                "tasting": {
                    "roast_level": "Medio",
                    "acidity": 9,
                    "body": 7,
                    "sweetness": 7,
                    "aroma": 8,
                    "flavor_notes": (
                        "Grosella negra, Pomelo rubí, Ciruela roja, Cacao"
                    ),
                },
            },
        ]

        for item in coffees:
            origin = Origin(
                country=item["origin"]["country"],
                region=item["origin"]["region"],
                farm=item["origin"]["farm"],
                altitude_meters=item["origin"]["altitude_meters"],
                process=item["origin"]["process"],
                variety=item["origin"]["variety"],
            )
            db.session.add(origin)
            db.session.flush()

            tasting = TastingProfile(
                roast_level=item["tasting"]["roast_level"],
                acidity=item["tasting"]["acidity"],
                body=item["tasting"]["body"],
                sweetness=item["tasting"]["sweetness"],
                aroma=item["tasting"]["aroma"],
                flavor_notes=item["tasting"]["flavor_notes"],
            )
            db.session.add(tasting)
            db.session.flush()

            product = Product(
                name=item["name"],
                slug=item["slug"],
                tagline=item["tagline"],
                description=item["description"],
                price=item["price"],
                stock=item["stock"],
                weight_grams=item["weight_grams"],
                image_url=item["image_url"],
                is_featured=item["is_featured"],
                origin_id=origin.id,
                tasting_profile_id=tasting.id,
            )
            db.session.add(product)

        db.session.commit()
