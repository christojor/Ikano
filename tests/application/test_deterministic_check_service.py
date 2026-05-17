from app.application.domain.onboarding import (
    CheckBusinessResultCode,
    CheckTechnicalResultCode,
    CheckTypeCode,
)
from app.application.services.deterministic_check_service import DeterministicCheckService


def test_each_check_type_uses_stable_adapter_name() -> None:
    service = DeterministicCheckService()

    results = {
        check_type: service.evaluate(check_type_code=check_type, payload={"scenario": "PASS"})
        for check_type in CheckTypeCode
    }

    assert results[CheckTypeCode.KYC].adapter_name == "KYC_DETERMINISTIC_ADAPTER"
    assert results[CheckTypeCode.KYB].adapter_name == "KYB_DETERMINISTIC_ADAPTER"
    assert results[CheckTypeCode.SANCTIONS].adapter_name == "SANCTIONS_DETERMINISTIC_ADAPTER"
    assert results[CheckTypeCode.CREDIT].adapter_name == "CREDIT_DETERMINISTIC_ADAPTER"
    assert results[CheckTypeCode.REGISTRY].adapter_name == "REGISTRY_DETERMINISTIC_ADAPTER"


def test_timeout_scenario_forces_manual_review_and_persists_technical_result() -> None:
    service = DeterministicCheckService()

    result = service.evaluate(
        check_type_code=CheckTypeCode.KYC,
        payload={"scenario": "PASS", "technical_scenario": "TIMEOUT"},
    )

    assert result.check_business_result_code == CheckBusinessResultCode.MANUAL_REVIEW
    assert result.check_technical_result_code == CheckTechnicalResultCode.TIMEOUT
    assert result.outcome_reason_code == "KYC_TIMEOUT"


def test_error_scenario_forces_fail_and_persists_technical_result() -> None:
    service = DeterministicCheckService()

    result = service.evaluate(
        check_type_code=CheckTypeCode.REGISTRY,
        payload={"scenario": "PASS", "technical_scenario": "ERROR"},
    )

    assert result.check_business_result_code == CheckBusinessResultCode.FAIL
    assert result.check_technical_result_code == CheckTechnicalResultCode.ERROR
    assert result.outcome_reason_code == "REGISTRY_ERROR"
