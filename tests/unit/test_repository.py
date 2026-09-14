from app.core.extensions import db
from app.models.origin import Origin
from app.repositories.base_repository import BaseRepository


def test_repository_persists_updates_and_deletes(app):
    with app.app_context():
        repo = BaseRepository(Origin)
        origin = Origin(country="Ecuador", region="Loja")
        repo.save(origin)
        identifier = origin.id
        assert repo.get_by_id(identifier).country == "Ecuador"
        assert origin in repo.get_all()
        origin.region = "Zamora"
        repo.commit()
        db.session.expire_all()
        assert repo.get_by_id(identifier).region == "Zamora"
        repo.delete(origin)
        assert repo.get_by_id(identifier) is None
