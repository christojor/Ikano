from typing import Protocol

from app.infrastructure.db.models.user import User


class UserRepository(Protocol):
    def get_by_id(self, user_id: int) -> User | None: ...
