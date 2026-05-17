from app.application.domain.onboarding import (
    CheckBusinessResultCode,
    CheckRunRecord,
    DecisionOutcomeCode,
    DecisionResult,
)
from app.application.ports.decision_evaluator_port import DecisionEvaluatorPort


RULE_VERSION = "decision-rules/v1"


class DecisionService(DecisionEvaluatorPort):
    def decide(self, check_runs: tuple[CheckRunRecord, ...]) -> DecisionResult:
        failed_checks = tuple(
            run.check_type_code.value
            for run in check_runs
            if run.check_business_result_code == CheckBusinessResultCode.FAIL
        )
        if failed_checks:
            return DecisionResult(
                outcome_code=DecisionOutcomeCode.REJECTED,
                reason_codes=("CHECK_FAILED", *tuple(f"{check}_FAILED" for check in failed_checks)),
                rule_version=RULE_VERSION,
                explanation={
                    "rule": "Any failed check rejects the application",
                    "failed_checks": ",".join(failed_checks),
                    "manual_review_checks": "",
                },
            )

        manual_review_checks = tuple(
            run.check_type_code.value
            for run in check_runs
            if run.check_business_result_code == CheckBusinessResultCode.MANUAL_REVIEW
        )
        if manual_review_checks:
            return DecisionResult(
                outcome_code=DecisionOutcomeCode.MANUAL_REVIEW,
                reason_codes=(
                    "CHECK_REQUIRES_MANUAL_REVIEW",
                    *tuple(f"{check}_MANUAL_REVIEW" for check in manual_review_checks),
                ),
                rule_version=RULE_VERSION,
                explanation={
                    "rule": "Manual-review checks escalate to human review",
                    "failed_checks": "",
                    "manual_review_checks": ",".join(manual_review_checks),
                },
            )

        return DecisionResult(
            outcome_code=DecisionOutcomeCode.APPROVED,
            reason_codes=("ALL_CHECKS_PASSED",),
            rule_version=RULE_VERSION,
            explanation={
                "rule": "Application is approved when all checks pass",
                "failed_checks": "",
                "manual_review_checks": "",
            },
        )
