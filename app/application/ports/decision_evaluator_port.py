from typing import Protocol

from app.application.domain.onboarding import CheckRunRecord, DecisionResult


class DecisionEvaluatorPort(Protocol):
    def decide(self, check_runs: tuple[CheckRunRecord, ...]) -> DecisionResult: ...
