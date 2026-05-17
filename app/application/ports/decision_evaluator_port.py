from typing import Protocol

from app.application.domain.onboarding import CheckRunRecord, DecisionOutcomeCode


class DecisionEvaluatorPort(Protocol):
    def decide(self, check_runs: tuple[CheckRunRecord, ...]) -> DecisionOutcomeCode:
        ...
