from app.services.product_service import ProductService


def test_get_hero_product(app):
    """Verifica que el servicio retorne un café destacado como Hero."""
    with app.app_context():
        service = ProductService()
        hero = service.get_hero_product()
        assert hero is not None
        assert hero.is_featured is True
        assert "Geisha" in hero.name or "Reserva" in hero.name


def test_get_featured_showcase(app):
    """Verifica que se obtengan los cafés destacados para la cuadrícula Bento."""
    with app.app_context():
        service = ProductService()
        featured = service.get_featured_showcase()
        assert len(featured) >= 1
        for p in featured:
            assert p.is_featured is True


def test_get_catalog_filtered_by_roast(app):
    """Verifica el filtrado de cafés por nivel de tueste."""
    with app.app_context():
        service = ProductService()
        claro_coffees = service.get_catalog(roast="Claro")
        assert len(claro_coffees) >= 1
        for c in claro_coffees:
            assert "Claro" in c.tasting_profile.roast_level


def test_get_by_slug(app):
    """Verifica la consulta de un café por su slug único."""
    with app.app_context():
        service = ProductService()
        coffee = service.get_by_slug("geisha-huila-reserva-privada")
        assert coffee is not None
        assert coffee.slug == "geisha-huila-reserva-privada"
        assert coffee.origin.country == "Colombia"


def test_get_radar_data(app):
    """Verifica que los datos del radar sensorial se calculen correctamente."""
    with app.app_context():
        service = ProductService()
        hero = service.get_hero_product()
        radar_data = service.get_radar_data(hero.id)
        assert radar_data is not None
        assert "radar" in radar_data
        assert "acidity" in radar_data["radar"]
        assert "notes" in radar_data["radar"]
        assert len(radar_data["radar"]["notes"]) > 0


def test_get_radar_data_non_existent(app):
    """Verifica el retorno seguro para un ID de producto inexistente."""
    with app.app_context():
        service = ProductService()
        assert service.get_radar_data(99999) is None
