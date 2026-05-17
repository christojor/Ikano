from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypeVar

from app.application.domain.exceptions import (
    ApplicationNotFoundError,
    NoActiveOnboardingFlowError,
    OnboardingFlowNotFoundError,
    UnsupportedCountryCodeError,
    UnsupportedPartyTypeCodeError,
)
from app.application.domain.onboarding import (
    ApplicationRecord,
    ApplicationStatus,
    AuditEvent,
    CheckRunRecord,
    CountryCode,
    DecisionOutcomeCode,
    ManualReviewCaseRecord,
    ManualReviewStatus,
    OnboardingFlow,
    PartyTypeCode,
)
from app.application.ports.check_evaluator_port import CheckEvaluatorPort
from app.application.ports.decision_evaluator_port import DecisionEvaluatorPort
from app.application.ports.onboarding_repository_port import OnboardingRepositoryPort
from app.application.ports.unit_of_work_port import NoOpUnitOfWork, UnitOfWorkPort
from app.application.services.application_progression_service import ApplicationProgressionService
from app.application.services.audit_trail_service import AuditTrailService
from app.application.services.decision_service import DecisionService
from app.application.services.deterministic_check_service import DeterministicCheckService

_TParsedCode = TypeVar("_TParsedCode")


class OnboardingService:
    def __init__(
        self,
        repository: OnboardingRepositoryPort,
        check_service: CheckEvaluatorPort | None = None,
        decision_service: DecisionEvaluatorPort | None = None,
        unit_of_work: UnitOfWorkPort | None = None,
        progression_service: ApplicationProgressionService | None = None,
    ) -> None:
        self._repository = repository
        self._check_service = check_service or DeterministicCheckService()
        self._decision_service = decision_service or DecisionService()
        self._unit_of_work = unit_of_work or NoOpUnitOfWork()
        self._progression_service = progression_service or ApplicationProgressionService()
        self._audit_service = AuditTrailService(audit_repository=self._repository)

    def start_application(self, country_code: str, party_type_code: str) -> ApplicationRecord:
        country = self._parse_country_code(country_code)
        party_type = self._parse_party_type_code(party_type_code)

        with self._unit_of_work.transaction():
            flow = self._repository.get_active_flow(country_code=country, party_type_code=party_type)
            if flow is None:
                raise NoActiveOnboardingFlowError("No active onboarding flow found")

            first_step = flow.steps[0]
            application_id = self._repository.next_application_id()
            now = datetime.now(UTC)
            application = ApplicationRecord(
                application_id=application_id,
                public_reference=f"APP-{application_id:06d}",
                country_code=country,
                party_type_code=party_type,
                flow_id=flow.flow_id,
                current_step_order=first_step.step_order,
                current_step_code=first_step.step_code,
                status=ApplicationStatus.IN_PROGRESS,
                created_at=now,
            )

            created = self._repository.create_application(application)

            self._audit_service.application_started(
                application_id=created.application_id,
                correlation_id=created.public_reference,
                event_timestamp=now,
                country_code=created.country_code.value,
                party_type_code=created.party_type_code.value,
                step_code=created.current_step_code,
            )

        return created

    def get_audit_events(self, application_id: int) -> tuple[AuditEvent, ...]:
        return self._repository.list_audit_events(application_id=application_id)

    def get_check_runs(self, application_id: int) -> tuple[CheckRunRecord, ...]:
        return self._repository.list_check_runs(application_id=application_id)

    def get_manual_review_case(self, application_id: int) -> ManualReviewCaseRecord | None:
        return self._repository.get_manual_review_case(application_id=application_id)

    def get_application(self, application_id: int) -> ApplicationRecord:
        application = self._repository.get_application(application_id=application_id)
        if application is None:
            raise ApplicationNotFoundError("Application not found")
        return application

    def get_flow_for_application(self, application_id: int) -> OnboardingFlow:
        _, flow = self._get_application_and_flow(application_id)
        return flow

    def advance_step(self, application_id: int, payload: dict[str, str]) -> ApplicationRecord:
        with self._unit_of_work.transaction():
            application, flow = self._get_application_and_flow(application_id)

            now = datetime.now(UTC)
            current_step = self._progression_service.get_current_step(application=application, flow=flow)

            self._audit_service.step_completed(
                application_id=application.application_id,
                correlation_id=application.public_reference,
                event_timestamp=now,
                step_code=current_step.step_code,
            )

            if current_step.check_type_code is not None:
                check_result = self._check_service.evaluate(payload=payload)
                check_run = CheckRunRecord(
                    check_run_id=self._repository.next_check_run_id(),
                    application_id=application.application_id,
                    check_type_code=current_step.check_type_code,
                    check_business_result_code=check_result,
                    correlation_id=application.public_reference,
                    input_fingerprint=payload.get("scenario", "PASS").upper(),
                    created_at=now,
                )
                self._repository.append_check_run(check_run)

                self._audit_service.check_completed(
                    application_id=application.application_id,
                    correlation_id=application.public_reference,
                    event_timestamp=now,
                    check_type_code=check_run.check_type_code.value,
                    check_business_result_code=check_run.check_business_result_code.value,
                )

            if self._progression_service.has_next_step(application=application, flow=flow):
                self._progression_service.move_to_next_step(application=application, flow=flow)
            else:
                decision = self._decision_service.decide(
                    check_runs=self._repository.list_check_runs(
                        application_id=application.application_id
                    )
                )
                self._finalize_application_decision(
                    application=application,
                    decision=decision,
                    decided_at=now,
                )

            self._repository.update_application(application)

        return application

    def _finalize_application_decision(
        self,
        *,
        application: ApplicationRecord,
        decision: DecisionOutcomeCode,
        decided_at: datetime,
    ) -> None:
        status_map = {
            DecisionOutcomeCode.APPROVED: ApplicationStatus.APPROVED,
            DecisionOutcomeCode.MANUAL_REVIEW: ApplicationStatus.UNDER_REVIEW,
            DecisionOutcomeCode.REJECTED: ApplicationStatus.REJECTED,
        }
        application.status = status_map[decision]
        application.submitted_at = decided_at

        self._audit_service.application_decided(
            application_id=application.application_id,
            correlation_id=application.public_reference,
            event_timestamp=decided_at,
            decision_outcome=decision.value,
        )

        if decision == DecisionOutcomeCode.MANUAL_REVIEW:
            manual_case = ManualReviewCaseRecord(
                manual_review_case_id=self._repository.next_manual_review_case_id(),
                application_id=application.application_id,
                review_status=ManualReviewStatus.OPEN,
                opened_at=decided_at,
            )
            self._repository.create_manual_review_case(manual_case)

            self._audit_service.manual_review_opened(
                application_id=application.application_id,
                correlation_id=application.public_reference,
                event_timestamp=decided_at,
                review_status=manual_case.review_status.value,
            )

    def _parse_country_code(self, country_code: str) -> CountryCode:
        return self._parse_code(
            value=country_code,
            parser=CountryCode,
            error_type=UnsupportedCountryCodeError,
            error_message="Unsupported country code",
        )

    def _parse_party_type_code(self, party_type_code: str) -> PartyTypeCode:
        return self._parse_code(
            value=party_type_code,
            parser=PartyTypeCode,
            error_type=UnsupportedPartyTypeCodeError,
            error_message="Unsupported party type code",
        )

    def _get_application_and_flow(self, application_id: int) -> tuple[ApplicationRecord, OnboardingFlow]:
        application = self._repository.get_application(application_id=application_id)
        if application is None:
            raise ApplicationNotFoundError("Application not found")

        flow = self._repository.get_flow_by_id(flow_id=application.flow_id)
        if flow is None:
            raise OnboardingFlowNotFoundError("Onboarding flow not found")
        return application, flow

    def _parse_code(
        self,
        *,
        value: str,
        parser: Callable[[str], _TParsedCode],
        error_type: type[Exception],
        error_message: str,
    ) -> _TParsedCode:
        try:
            return parser(value.upper())
        except ValueError as error:
            raise error_type(error_message) from error
