from datetime import UTC, datetime

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
    PartyTypeCode,
)
from app.application.ports.application_repository_port import ApplicationRepositoryPort
from app.application.ports.audit_event_repository_port import AuditEventRepositoryPort
from app.application.ports.check_evaluator_port import CheckEvaluatorPort
from app.application.ports.check_run_repository_port import CheckRunRepositoryPort
from app.application.ports.decision_evaluator_port import DecisionEvaluatorPort
from app.application.ports.flow_query_port import FlowQueryPort
from app.application.ports.manual_review_repository_port import ManualReviewRepositoryPort
from app.application.ports.unit_of_work_port import NoOpUnitOfWork, UnitOfWorkPort
from app.application.services.application_progression_service import ApplicationProgressionService
from app.application.services.audit_trail_service import AuditTrailService
from app.application.services.decision_service import DecisionService
from app.application.services.deterministic_check_service import DeterministicCheckService


class OnboardingService:
    def __init__(
        self,
        flow_query: FlowQueryPort,
        application_repository: ApplicationRepositoryPort,
        audit_repository: AuditEventRepositoryPort,
        check_run_repository: CheckRunRepositoryPort,
        manual_review_repository: ManualReviewRepositoryPort,
        check_service: CheckEvaluatorPort | None = None,
        decision_service: DecisionEvaluatorPort | None = None,
        unit_of_work: UnitOfWorkPort | None = None,
        progression_service: ApplicationProgressionService | None = None,
    ) -> None:
        self._flow_query = flow_query
        self._application_repository = application_repository
        self._audit_repository = audit_repository
        self._check_run_repository = check_run_repository
        self._manual_review_repository = manual_review_repository
        self._check_service = check_service or DeterministicCheckService()
        self._decision_service = decision_service or DecisionService()
        self._unit_of_work = unit_of_work or NoOpUnitOfWork()
        self._progression_service = progression_service or ApplicationProgressionService()
        self._audit_service = AuditTrailService(audit_repository=self._audit_repository)

    def start_application(self, country_code: str, party_type_code: str) -> ApplicationRecord:
        country = self._parse_country_code(country_code)
        party_type = self._parse_party_type_code(party_type_code)

        with self._unit_of_work.transaction():
            flow = self._flow_query.get_active_flow(
                country_code=country, party_type_code=party_type
            )
            if flow is None:
                raise NoActiveOnboardingFlowError("No active onboarding flow found")

            first_step = flow.steps[0]
            application_id = self._application_repository.next_application_id()
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

            created = self._application_repository.create_application(application)

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
        return self._audit_repository.list_audit_events(application_id=application_id)

    def get_check_runs(self, application_id: int) -> tuple[CheckRunRecord, ...]:
        return self._check_run_repository.list_check_runs(application_id=application_id)

    def get_manual_review_case(self, application_id: int) -> ManualReviewCaseRecord | None:
        return self._manual_review_repository.get_manual_review_case(application_id=application_id)

    def get_application(self, application_id: int) -> ApplicationRecord:
        application = self._application_repository.get_application(application_id=application_id)
        if application is None:
            raise ApplicationNotFoundError("Application not found")
        return application

    def advance_step(self, application_id: int, payload: dict[str, str]) -> ApplicationRecord:
        with self._unit_of_work.transaction():
            application = self._application_repository.get_application(
                application_id=application_id
            )
            if application is None:
                raise ApplicationNotFoundError("Application not found")

            flow = self._flow_query.get_flow_by_id(flow_id=application.flow_id)
            if flow is None:
                raise OnboardingFlowNotFoundError("Onboarding flow not found")

            now = datetime.now(UTC)
            current_step = self._progression_service.get_current_step(
                application=application, flow=flow
            )

            self._audit_service.step_completed(
                application_id=application.application_id,
                correlation_id=application.public_reference,
                event_timestamp=now,
                step_code=current_step.step_code,
            )

            if current_step.check_type_code is not None:
                check_result = self._check_service.evaluate(payload=payload)
                check_run = CheckRunRecord(
                    check_run_id=self._check_run_repository.next_check_run_id(),
                    application_id=application.application_id,
                    check_type_code=current_step.check_type_code,
                    check_business_result_code=check_result,
                    correlation_id=application.public_reference,
                    input_fingerprint=payload.get("scenario", "PASS").upper(),
                    created_at=now,
                )
                self._check_run_repository.append_check_run(check_run)

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
                    check_runs=self._check_run_repository.list_check_runs(
                        application_id=application.application_id
                    )
                )
                self._finalize_application_decision(
                    application=application,
                    decision=decision,
                    decided_at=now,
                )

            self._application_repository.update_application(application)

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
                manual_review_case_id=self._manual_review_repository.next_manual_review_case_id(),
                application_id=application.application_id,
                review_status=ManualReviewStatus.OPEN,
                opened_at=decided_at,
            )
            self._manual_review_repository.create_manual_review_case(manual_case)

            self._audit_service.manual_review_opened(
                application_id=application.application_id,
                correlation_id=application.public_reference,
                event_timestamp=decided_at,
                review_status=manual_case.review_status.value,
            )

    def _parse_country_code(self, country_code: str) -> CountryCode:
        try:
            return CountryCode(country_code.upper())
        except ValueError as error:
            raise UnsupportedCountryCodeError("Unsupported country code") from error

    def _parse_party_type_code(self, party_type_code: str) -> PartyTypeCode:
        try:
            return PartyTypeCode(party_type_code.upper())
        except ValueError as error:
            raise UnsupportedPartyTypeCodeError("Unsupported party type code") from error
