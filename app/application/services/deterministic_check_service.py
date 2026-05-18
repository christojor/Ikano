from dataclasses import dataclass

from app.application.domain.onboarding import (
    CheckBusinessResultCode,
    CheckEvaluationResult,
    CheckTechnicalResultCode,
    CheckTypeCode,
)
from app.application.ports.check_evaluator_port import CheckEvaluatorPort


@dataclass(slots=True, frozen=True)
class _CheckAdapter:
    check_type_code: CheckTypeCode
    adapter_name: str

    def evaluate(self, payload: dict[str, str]) -> CheckEvaluationResult:
        technical = _parse_technical_result(payload)
        if technical == CheckTechnicalResultCode.TIMEOUT:
            return CheckEvaluationResult(
                check_business_result_code=CheckBusinessResultCode.MANUAL_REVIEW,
                check_technical_result_code=technical,
                adapter_name=self.adapter_name,
                outcome_reason_code=f"{self.check_type_code.value}_TIMEOUT",
            )

        if technical == CheckTechnicalResultCode.ERROR:
            return CheckEvaluationResult(
                check_business_result_code=CheckBusinessResultCode.FAIL,
                check_technical_result_code=technical,
                adapter_name=self.adapter_name,
                outcome_reason_code=f"{self.check_type_code.value}_ERROR",
            )

        scenario = payload.get("scenario", "PASS").upper()
        business_result = _parse_business_result(scenario)
        return CheckEvaluationResult(
            check_business_result_code=business_result,
            check_technical_result_code=technical,
            adapter_name=self.adapter_name,
            outcome_reason_code=f"{self.check_type_code.value}_{business_result.value}",
        )


class DeterministicCheckService(CheckEvaluatorPort):
    def __init__(self) -> None:
        self._adapters = {
            CheckTypeCode.KYC: _CheckAdapter(CheckTypeCode.KYC, "KYC_DETERMINISTIC_ADAPTER"),
            CheckTypeCode.KYB: _CheckAdapter(CheckTypeCode.KYB, "KYB_DETERMINISTIC_ADAPTER"),
            CheckTypeCode.SANCTIONS: _CheckAdapter(
                CheckTypeCode.SANCTIONS,
                "SANCTIONS_DETERMINISTIC_ADAPTER",
            ),
            CheckTypeCode.CREDIT: _CheckAdapter(CheckTypeCode.CREDIT, "CREDIT_DETERMINISTIC_ADAPTER"),
            CheckTypeCode.REGISTRY: _CheckAdapter(
                CheckTypeCode.REGISTRY,
                "REGISTRY_DETERMINISTIC_ADAPTER",
            ),
            CheckTypeCode.ADDRESS: _CheckAdapter(
                CheckTypeCode.ADDRESS,
                "ADDRESS_DETERMINISTIC_ADAPTER",
            ),
            CheckTypeCode.BANK: _CheckAdapter(CheckTypeCode.BANK, "BANK_DETERMINISTIC_ADAPTER"),
        }

    def evaluate(
        self,
        *,
        check_type_code: CheckTypeCode,
        payload: dict[str, str],
    ) -> CheckEvaluationResult:
        adapter = self._adapters[check_type_code]
        return adapter.evaluate(payload)


def _parse_business_result(value: str) -> CheckBusinessResultCode:
    if value == CheckBusinessResultCode.MANUAL_REVIEW.value:
        return CheckBusinessResultCode.MANUAL_REVIEW
    if value == CheckBusinessResultCode.FAIL.value:
        return CheckBusinessResultCode.FAIL
    return CheckBusinessResultCode.PASS


def _parse_technical_result(payload: dict[str, str]) -> CheckTechnicalResultCode:
    value = payload.get("technical_scenario", "OK").upper()
    if value == CheckTechnicalResultCode.TIMEOUT.value:
        return CheckTechnicalResultCode.TIMEOUT
    if value == CheckTechnicalResultCode.ERROR.value:
        return CheckTechnicalResultCode.ERROR
    return CheckTechnicalResultCode.OK
