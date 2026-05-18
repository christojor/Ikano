from collections.abc import Callable
from typing import ClassVar

from app.application.domain.exceptions import InvalidStepPayloadError
from app.application.domain.onboarding import CheckTypeCode


class StepPayloadValidationService:
    """Validates per-step payload fields used to advance onboarding flows."""

    _SCENARIOS: ClassVar[set[str]] = {"PASS", "FAIL", "MANUAL_REVIEW"}
    _TECHNICAL_SCENARIOS: ClassVar[set[str]] = {"OK", "TIMEOUT", "ERROR"}

    def validate(
        self,
        *,
        step_code: str,
        payload: dict[str, str],
        check_type_code: CheckTypeCode | None,
    ) -> None:
        if check_type_code is not None:
            self._validate_scenario(payload)
            self._validate_technical_scenario(payload)

        step_validators: dict[str, Callable[[dict[str, str]], None]] = {
            "COLLECT_SE_IDENTITY": self._validate_collect_se_identity,
            "COLLECT_ES_DNI_NIE": self._validate_collect_es_identity,
            "COLLECT_PL_PESEL": self._validate_collect_pl_pesel,
            "CONFIRM_SE_CONTACT": self._validate_confirm_contact,
            "CONFIRM_ES_CONTACT": self._validate_confirm_contact,
            "CONFIRM_PL_CONTACT": self._validate_confirm_contact,
            "COLLECT_SE_AFFORD": self._validate_collect_affordability,
            "COLLECT_ES_AFFORD": self._validate_collect_affordability,
            "COLLECT_PL_AFFORD": self._validate_collect_affordability,
            "COLLECT_BUSINESS_PROFILE": self._validate_collect_business_profile,
            "VERIFY_BUSINESS_REPRESENTATIVE": self._validate_verify_business_representative,
            "CAPTURE_BUSINESS_OWNERSHIP": self._validate_capture_business_ownership,
            "RUN_SE_CREDIT": self._validate_credit_inputs,
            "RUN_ES_CREDIT": self._validate_credit_inputs,
            "RUN_PL_BIK": self._validate_credit_inputs,
            "RUN_BUSINESS_CREDIT": self._validate_credit_inputs,
            "REVIEW_SE_SUBMIT": self._validate_review_submit,
            "REVIEW_ES_SUBMIT": self._validate_review_submit,
            "REVIEW_PL_SUBMIT": self._validate_review_submit,
            "REVIEW_BUSINESS_SUBMIT": self._validate_review_business_submit,
        }

        validator = step_validators.get(step_code)
        if validator is None:
            return

        validator(payload)

    def _validate_scenario(self, payload: dict[str, str]) -> None:
        scenario = payload.get("scenario", "PASS").upper()
        if scenario not in self._SCENARIOS:
            raise InvalidStepPayloadError("Scenario must be PASS, FAIL, or MANUAL_REVIEW")

    def _validate_technical_scenario(self, payload: dict[str, str]) -> None:
        technical_scenario = payload.get("technical_scenario", "OK").upper()
        if technical_scenario not in self._TECHNICAL_SCENARIOS:
            raise InvalidStepPayloadError("technical_scenario must be OK, TIMEOUT, or ERROR")

    def _validate_collect_se_identity(self, payload: dict[str, str]) -> None:
        self._require_digits(payload, field="identity_number", expected_lengths={10, 12})

    def _validate_collect_es_identity(self, payload: dict[str, str]) -> None:
        self._require_alnum(payload, field="identity_number", min_len=8, max_len=12)

    def _validate_collect_pl_pesel(self, payload: dict[str, str]) -> None:
        self._require_digits(payload, field="identity_number", expected_lengths={11})

    def _validate_confirm_contact(self, payload: dict[str, str]) -> None:
        self._require_email(payload, field="email")

    def _validate_collect_affordability(self, payload: dict[str, str]) -> None:
        self._require_positive_int(payload, field="monthly_income")

    def _validate_collect_business_profile(self, payload: dict[str, str]) -> None:
        self._require_alnum(payload, field="organization_number", min_len=6, max_len=20)

    def _validate_verify_business_representative(self, payload: dict[str, str]) -> None:
        self._require_alnum(payload, field="representative_identity", min_len=6, max_len=20)

    def _validate_capture_business_ownership(self, payload: dict[str, str]) -> None:
        self._require_alnum(payload, field="ubo_identifier", min_len=6, max_len=24)

    def _validate_credit_inputs(self, payload: dict[str, str]) -> None:
        self._require_positive_int(payload, field="monthly_income")
        self._require_positive_int(payload, field="monthly_expenses")

    def _validate_review_submit(self, payload: dict[str, str]) -> None:
        if payload.get("accept_terms", "").lower() not in {"true", "1", "yes", "on"}:
            raise InvalidStepPayloadError("Terms must be accepted before submission")

    def _validate_review_business_submit(self, payload: dict[str, str]) -> None:
        self._validate_review_submit(payload)
        self._require_alnum(payload, field="bank_iban", min_len=10, max_len=34)

    def _require_value(self, payload: dict[str, str], *, field: str) -> str:
        value = payload.get(field, "").strip()
        if not value:
            raise InvalidStepPayloadError(f"{field} is required")
        return value

    def _require_digits(
        self,
        payload: dict[str, str],
        *,
        field: str,
        expected_lengths: set[int],
    ) -> None:
        value = self._require_value(payload, field=field)
        if not value.isdigit() or len(value) not in expected_lengths:
            raise InvalidStepPayloadError(f"{field} has an invalid format")

    def _require_alnum(
        self,
        payload: dict[str, str],
        *,
        field: str,
        min_len: int,
        max_len: int,
    ) -> None:
        value = self._require_value(payload, field=field)
        if not value.replace("-", "").isalnum() or not (min_len <= len(value) <= max_len):
            raise InvalidStepPayloadError(f"{field} has an invalid format")

    def _require_email(self, payload: dict[str, str], *, field: str) -> None:
        value = self._require_value(payload, field=field)
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise InvalidStepPayloadError(f"{field} has an invalid format")

    def _require_positive_int(self, payload: dict[str, str], *, field: str) -> None:
        value = self._require_value(payload, field=field)
        if not value.isdigit() or int(value) <= 0:
            raise InvalidStepPayloadError(f"{field} must be a positive number")
