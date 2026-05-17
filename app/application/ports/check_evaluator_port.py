from typing import Protocol

from app.application.domain.onboarding import (
    CheckEvaluationResult,
    CheckTypeCode,
)


class CheckEvaluatorPort(Protocol):
    def evaluate(
        self,
        *,
        check_type_code: CheckTypeCode,
        payload: dict[str, str],
    ) -> CheckEvaluationResult: ...
