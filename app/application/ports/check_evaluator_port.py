from typing import Protocol

from app.application.domain.onboarding import CheckBusinessResultCode


class CheckEvaluatorPort(Protocol):
    def evaluate(self, payload: dict[str, str]) -> CheckBusinessResultCode:
        ...
