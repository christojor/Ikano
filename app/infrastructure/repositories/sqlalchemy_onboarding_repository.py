from datetime import UTC

from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.application.domain.onboarding import (
    ActorType,
    ApplicationRecord,
    ApplicationStatus,
    AuditEvent,
    AuditEventType,
    CheckBusinessResultCode,
    CheckRunRecord,
    CheckTypeCode,
    CountryCode,
    ManualReviewCaseRecord,
    ManualReviewStatus,
    OnboardingFlow,
    OnboardingStep,
    PartyTypeCode,
)
from app.infrastructure.db.models.onboarding import (
    ApplicationModel,
    AuditEventModel,
    CheckRunModel,
    ManualReviewCaseModel,
    OnboardingFlowModel,
    OnboardingStepModel,
)


class SQLAlchemyOnboardingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_active_flow(
        self, country_code: CountryCode, party_type_code: PartyTypeCode
    ) -> OnboardingFlow | None:
        model = (
            self._session.query(OnboardingFlowModel)
            .options(selectinload(OnboardingFlowModel.steps))
            .filter(
                OnboardingFlowModel.country_code == country_code.value,
                OnboardingFlowModel.party_type_code == party_type_code.value,
                OnboardingFlowModel.is_active.is_(True),
            )
            .order_by(OnboardingFlowModel.flow_version.desc())
            .first()
        )
        if model is None:
            return None
        return self._to_flow(model)

    def get_flow_by_id(self, flow_id: int) -> OnboardingFlow | None:
        model = (
            self._session.query(OnboardingFlowModel)
            .options(selectinload(OnboardingFlowModel.steps))
            .filter(OnboardingFlowModel.flow_id == flow_id)
            .first()
        )
        if model is None:
            return None
        return self._to_flow(model)

    def create_application(self, application: ApplicationRecord) -> ApplicationRecord:
        current_step_id = self._find_step_id(
            flow_id=application.flow_id, step_code=application.current_step_code
        )
        model = ApplicationModel(
            application_id=application.application_id,
            public_reference=application.public_reference,
            country_code=application.country_code.value,
            party_type_code=application.party_type_code.value,
            flow_id=application.flow_id,
            application_status_code=application.status.value,
            current_step_id=current_step_id,
            submitted_at=application.submitted_at,
        )
        self._session.add(model)
        self._session.flush()
        return self._to_application(model)

    def get_application(self, application_id: int) -> ApplicationRecord | None:
        model = (
            self._session.query(ApplicationModel)
            .filter(ApplicationModel.application_id == application_id)
            .first()
        )
        if model is None:
            return None
        return self._to_application(model)

    def update_application(self, application: ApplicationRecord) -> None:
        model = (
            self._session.query(ApplicationModel)
            .filter(ApplicationModel.application_id == application.application_id)
            .first()
        )
        if model is None:
            return

        model.application_status_code = application.status.value
        model.current_step_id = self._find_step_id(
            flow_id=application.flow_id, step_code=application.current_step_code
        )
        model.submitted_at = application.submitted_at
        self._session.flush()

    def next_application_id(self) -> int:
        return self._next_sequence_value(table_name="application", column_name="application_id")

    def append_audit_event(self, event: AuditEvent) -> None:
        self._session.add(
            AuditEventModel(
                application_id=event.application_id,
                actor_type=event.actor_type.value,
                actor_id=event.actor_id,
                event_type=event.event_type.value,
                event_timestamp=event.event_timestamp,
                correlation_id=event.correlation_id,
                metadata_json=event.metadata,
            )
        )
        self._session.flush()

    def list_audit_events(self, application_id: int) -> tuple[AuditEvent, ...]:
        models = (
            self._session.query(AuditEventModel)
            .filter(AuditEventModel.application_id == application_id)
            .order_by(AuditEventModel.audit_event_id.asc())
            .all()
        )
        return tuple(
            AuditEvent(
                application_id=model.application_id,
                event_type=AuditEventType(model.event_type),
                event_timestamp=model.event_timestamp,
                actor_type=ActorType(model.actor_type),
                actor_id=model.actor_id,
                correlation_id=model.correlation_id,
                metadata=model.metadata_json or {},
            )
            for model in models
        )

    def next_check_run_id(self) -> int:
        return self._next_sequence_value(table_name="check_run", column_name="check_run_id")

    def append_check_run(self, check_run: CheckRunRecord) -> None:
        self._session.add(
            CheckRunModel(
                check_run_id=check_run.check_run_id,
                application_id=check_run.application_id,
                check_type_code=check_run.check_type_code.value,
                correlation_id=check_run.correlation_id,
                input_fingerprint=check_run.input_fingerprint,
                created_at=check_run.created_at,
                check_business_result_code=check_run.check_business_result_code.value,
            )
        )
        self._session.flush()

    def list_check_runs(self, application_id: int) -> tuple[CheckRunRecord, ...]:
        models = (
            self._session.query(CheckRunModel)
            .filter(CheckRunModel.application_id == application_id)
            .order_by(CheckRunModel.check_run_id.asc())
            .all()
        )
        return tuple(
            CheckRunRecord(
                check_run_id=model.check_run_id,
                application_id=model.application_id,
                check_type_code=CheckTypeCode(model.check_type_code),
                check_business_result_code=CheckBusinessResultCode(
                    model.check_business_result_code or CheckBusinessResultCode.PASS.value
                ),
                correlation_id=model.correlation_id,
                input_fingerprint=model.input_fingerprint,
                created_at=model.created_at,
            )
            for model in models
        )

    def next_manual_review_case_id(self) -> int:
        return self._next_sequence_value(
            table_name="manual_review_case",
            column_name="manual_review_case_id",
        )

    def create_manual_review_case(self, case: ManualReviewCaseRecord) -> ManualReviewCaseRecord:
        model = ManualReviewCaseModel(
            manual_review_case_id=case.manual_review_case_id,
            application_id=case.application_id,
            review_status=case.review_status.value,
            opened_at=case.opened_at,
        )
        self._session.add(model)
        self._session.flush()
        return self._to_manual_review_case(model)

    def get_manual_review_case(self, application_id: int) -> ManualReviewCaseRecord | None:
        model = (
            self._session.query(ManualReviewCaseModel)
            .filter(ManualReviewCaseModel.application_id == application_id)
            .first()
        )
        if model is None:
            return None
        return self._to_manual_review_case(model)

    def _next_sequence_value(self, *, table_name: str, column_name: str) -> int:
        query = text("SELECT nextval(pg_get_serial_sequence(:table_name, :column_name))")
        return int(
            self._session.execute(
                query,
                {"table_name": table_name, "column_name": column_name},
            ).scalar_one()
        )

    def _find_step_id(self, flow_id: int, step_code: str) -> int | None:
        model = (
            self._session.query(OnboardingStepModel)
            .filter(
                OnboardingStepModel.flow_id == flow_id,
                OnboardingStepModel.step_code == step_code,
            )
            .first()
        )
        return None if model is None else model.step_id

    def _to_flow(self, model: OnboardingFlowModel) -> OnboardingFlow:
        steps = tuple(
            self._to_step(step) for step in sorted(model.steps, key=lambda item: item.step_order)
        )
        return OnboardingFlow(
            flow_id=model.flow_id,
            country_code=CountryCode(model.country_code),
            party_type_code=PartyTypeCode(model.party_type_code),
            steps=steps,
            is_active=model.is_active,
        )

    def _to_step(self, model: OnboardingStepModel) -> OnboardingStep:
        check_type = None if model.check_type_code is None else CheckTypeCode(model.check_type_code)
        return OnboardingStep(
            step_code=model.step_code,
            step_title=model.step_title,
            step_order=model.step_order,
            check_type_code=check_type,
        )

    def _to_manual_review_case(self, model: ManualReviewCaseModel) -> ManualReviewCaseRecord:
        return ManualReviewCaseRecord(
            manual_review_case_id=model.manual_review_case_id,
            application_id=model.application_id,
            review_status=ManualReviewStatus(model.review_status),
            opened_at=model.opened_at,
        )

    def _to_application(self, model: ApplicationModel) -> ApplicationRecord:
        step_model = None
        if model.current_step_id is not None:
            step_model = (
                self._session.query(OnboardingStepModel)
                .filter(OnboardingStepModel.step_id == model.current_step_id)
                .first()
            )

        if step_model is None:
            step_model = (
                self._session.query(OnboardingStepModel)
                .filter(OnboardingStepModel.flow_id == model.flow_id)
                .order_by(OnboardingStepModel.step_order.asc())
                .first()
            )

        if step_model is None:
            raise ValueError("No onboarding step found for application flow")

        return ApplicationRecord(
            application_id=model.application_id,
            public_reference=model.public_reference,
            country_code=CountryCode(model.country_code),
            party_type_code=PartyTypeCode(model.party_type_code),
            flow_id=model.flow_id,
            current_step_order=step_model.step_order,
            current_step_code=step_model.step_code,
            status=ApplicationStatus(model.application_status_code),
            created_at=model.created_at.replace(tzinfo=UTC),
            submitted_at=None
            if model.submitted_at is None
            else model.submitted_at.replace(tzinfo=UTC),
        )
