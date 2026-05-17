from typing import Protocol

from app.application.domain.onboarding import ApplicationStepRecord


class ApplicationStepRepositoryPort(Protocol):
    def next_application_step_id(self) -> int:
        ...

    def append_application_step(self, application_step: ApplicationStepRecord) -> None:
        ...

    def list_application_steps(self, application_id: int) -> tuple[ApplicationStepRecord, ...]:
        ...
