from contextlib import AbstractContextManager
from typing import Literal

from sqlalchemy.orm import Session


class SQLAlchemyUnitOfWork:
    class _TransactionContext:
        def __init__(self, session: Session) -> None:
            self._session = session

        def __enter__(self) -> None:
            return None

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            traceback: object | None,
        ) -> Literal[False]:
            if exc_type is not None:
                self._session.rollback()
                return False
            self._session.commit()
            return False

    def __init__(self, session: Session) -> None:
        self._session = session

    def transaction(self) -> AbstractContextManager[None]:
        return self._TransactionContext(self._session)
