from app.application.domain.onboarding import (
    CheckBusinessResultCode,
    CheckRunRecord,
    DecisionOutcomeCode,
)
from app.application.ports.decision_evaluator_port import DecisionEvaluatorPort


class DecisionService(DecisionEvaluatorPort):
    def decide(self, check_runs: tuple[CheckRunRecord, ...]) -> DecisionOutcomeCode:
        if any(
            run.check_business_result_code == CheckBusinessResultCode.FAIL for run in check_runs
        ):
            return DecisionOutcomeCode.REJECTED

        if any(
            run.check_business_result_code == CheckBusinessResultCode.MANUAL_REVIEW
            for run in check_runs
        ):
            return DecisionOutcomeCode.MANUAL_REVIEW

        return DecisionOutcomeCode.APPROVED
