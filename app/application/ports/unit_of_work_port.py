from contextlib import AbstractContextManager
from typing import Literal, Protocol


class UnitOfWorkPort(Protocol):
    def transaction(self) -> AbstractContextManager[None]:
        ...


class NoOpUnitOfWork:
    class _TransactionContext:
        def __enter__(self) -> None:
            return None

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            traceback: object | None,
        ) -> Literal[False]:
            return False

    def transaction(self) -> AbstractContextManager[None]:
        return self._TransactionContext()
