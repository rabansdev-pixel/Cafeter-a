from typing import Type, TypeVar, Generic, List, Optional
from app.core.extensions import db

T = TypeVar("T", bound=db.Model)


class BaseRepository(Generic[T]):
    """Repositorio base con operaciones CRUD genéricas y seguras."""

    def __init__(self, model: Type[T]):
        self.model = model

    def get_by_id(self, id: int) -> Optional[T]:
        return db.session.get(self.model, id)

    def get_all(self) -> List[T]:
        return self.model.query.all()

    def save(self, entity: T) -> T:
        db.session.add(entity)
        db.session.commit()
        return entity

    def delete(self, entity: T) -> None:
        db.session.delete(entity)
        db.session.commit()

    def commit(self) -> None:
        db.session.commit()
