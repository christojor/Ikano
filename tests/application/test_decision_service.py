from datetime import UTC, datetime

from app.application.domain.onboarding import (
    CheckBusinessResultCode,
    CheckRunRecord,
    CheckTypeCode,
    DecisionOutcomeCode,
)
from app.application.services.decision_service import DecisionService, RULE_VERSION


def _check_run(
    check_type: CheckTypeCode,
    business_result: CheckBusinessResultCode,
    check_run_id: int,
) -> CheckRunRecord:
    return CheckRunRecord(
        check_run_id=check_run_id,
        application_id=1,
        check_type_code=check_type,
        check_business_result_code=business_result,
        correlation_id="APP-000001",
        input_fingerprint="PASS:OK",
        created_at=datetime.now(UTC),
    )


def test_decision_rejects_when_any_check_fails() -> None:
    service = DecisionService()

    result = service.decide(
        (
            _check_run(CheckTypeCode.KYC, CheckBusinessResultCode.PASS, 1),
            _check_run(CheckTypeCode.SANCTIONS, CheckBusinessResultCode.FAIL, 2),
        )
    )

    assert result.outcome_code == DecisionOutcomeCode.REJECTED
    assert result.reason_codes == ("CHECK_FAILED", "SANCTIONS_FAILED")
    assert result.rule_version == RULE_VERSION


def test_decision_escalates_manual_review_when_no_fails_and_manual_present() -> None:
    service = DecisionService()

    result = service.decide(
        (
            _check_run(CheckTypeCode.KYC, CheckBusinessResultCode.PASS, 1),
            _check_run(CheckTypeCode.CREDIT, CheckBusinessResultCode.MANUAL_REVIEW, 2),
        )
    )

    assert result.outcome_code == DecisionOutcomeCode.MANUAL_REVIEW
    assert result.reason_codes == (
        "CHECK_REQUIRES_MANUAL_REVIEW",
        "CREDIT_MANUAL_REVIEW",
    )
    assert result.rule_version == RULE_VERSION


def test_decision_approves_when_all_checks_pass() -> None:
    service = DecisionService()

    result = service.decide(
        (
            _check_run(CheckTypeCode.KYC, CheckBusinessResultCode.PASS, 1),
            _check_run(CheckTypeCode.SANCTIONS, CheckBusinessResultCode.PASS, 2),
            _check_run(CheckTypeCode.CREDIT, CheckBusinessResultCode.PASS, 3),
        )
    )

    assert result.outcome_code == DecisionOutcomeCode.APPROVED
    assert result.reason_codes == ("ALL_CHECKS_PASSED",)
    assert result.rule_version == RULE_VERSION
