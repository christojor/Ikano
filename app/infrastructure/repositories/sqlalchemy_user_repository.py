from sqlalchemy.orm import Session

from app.application.ports.user_repository import UserRepository
from app.infrastructure.db.models.user import User


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: int) -> User | None:
        return self._session.get(User, user_id)
