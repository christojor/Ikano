from app.application.domain.onboarding import CheckBusinessResultCode
from app.application.ports.check_evaluator_port import CheckEvaluatorPort


class DeterministicCheckService(CheckEvaluatorPort):
    def evaluate(self, payload: dict[str, str]) -> CheckBusinessResultCode:
        scenario = payload.get("scenario", "PASS").upper()
        if scenario == CheckBusinessResultCode.MANUAL_REVIEW.value:
            return CheckBusinessResultCode.MANUAL_REVIEW
        if scenario == CheckBusinessResultCode.FAIL.value:
            return CheckBusinessResultCode.FAIL
        return CheckBusinessResultCode.PASS
