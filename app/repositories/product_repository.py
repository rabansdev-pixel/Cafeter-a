from typing import List, Optional
from app.repositories.base_repository import BaseRepository
from app.models.product import Product
from app.models.origin import Origin
from app.models.tasting_note import TastingProfile


class ProductRepository(BaseRepository[Product]):
    """Repositorio especializado en consultas de productos de café."""

    def __init__(self):
        super().__init__(Product)

    def get_by_slug(self, slug: str) -> Optional[Product]:
        return Product.query.filter_by(slug=slug, is_active=True).first()

    def get_featured(self) -> List[Product]:
        return Product.query.filter_by(is_featured=True, is_active=True, menu_id=None).all()

    def get_all_active(self) -> List[Product]:
        return Product.query.filter_by(is_active=True, menu_id=None).all()

    def filter_products(
        self, roast: Optional[str] = None, country: Optional[str] = None
    ) -> List[Product]:
        """
        Filtra productos usando parámetros enlazados seguros con icontains y autoescape
        para prevenir inyección SQL (Snyk CWE-89).
        """
        query = (
            Product.query.join(Origin)
            .join(TastingProfile)
            .filter(Product.is_active.is_(True))
        )

        if roast:
            query = query.filter(
                TastingProfile.roast_level.icontains(roast.strip(), autoescape=True)
            )

        if country:
            query = query.filter(
                Origin.country.icontains(country.strip(), autoescape=True)
            )

        return query.all()
