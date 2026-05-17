from typing import Protocol

from app.application.domain.onboarding import CheckRunRecord


class CheckRunRepositoryPort(Protocol):
    def next_check_run_id(self) -> int: ...

    def append_check_run(self, check_run: CheckRunRecord) -> None: ...

    def list_check_runs(self, application_id: int) -> tuple[CheckRunRecord, ...]: ...
