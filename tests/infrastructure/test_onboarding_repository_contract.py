from datetime import UTC, datetime

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
    PartyTypeCode,
)
from app.infrastructure.repositories.in_memory_onboarding_repository import (
    InMemoryOnboardingRepository,
)


def test_repository_contract_supports_core_persistence_roundtrip() -> None:
    repo = InMemoryOnboardingRepository()
    now = datetime.now(UTC)

    app = ApplicationRecord(
        application_id=repo.next_application_id(),
        public_reference="APP-000001",
        country_code=CountryCode.SE,
        party_type_code=PartyTypeCode.PRIVATE,
        flow_id=1,
        current_step_order=1,
        current_step_code="COLLECT_PRIVATE_PROFILE",
        status=ApplicationStatus.IN_PROGRESS,
        created_at=now,
    )

    repo.create_application(app)
    loaded = repo.get_application(app.application_id)

    assert loaded is not None
    assert loaded.public_reference == "APP-000001"


def test_repository_contract_supports_audit_check_and_manual_review_records() -> None:
    repo = InMemoryOnboardingRepository()
    now = datetime.now(UTC)

    application_id = repo.next_application_id()
    correlation_id = "APP-000001"

    repo.append_audit_event(
        AuditEvent(
            application_id=application_id,
            event_type=AuditEventType.APPLICATION_STARTED,
            event_timestamp=now,
            actor_type=ActorType.SYSTEM,
            actor_id="contract-test",
            correlation_id=correlation_id,
            metadata={"step_code": "COLLECT_PRIVATE_PROFILE"},
        )
    )

    repo.append_check_run(
        CheckRunRecord(
            check_run_id=repo.next_check_run_id(),
            application_id=application_id,
            check_type_code=CheckTypeCode.KYC,
            check_business_result_code=CheckBusinessResultCode.PASS,
            correlation_id=correlation_id,
            input_fingerprint="PASS",
            created_at=now,
        )
    )

    repo.create_manual_review_case(
        ManualReviewCaseRecord(
            manual_review_case_id=repo.next_manual_review_case_id(),
            application_id=application_id,
            review_status=ManualReviewStatus.OPEN,
            opened_at=now,
        )
    )

    assert (
        repo.list_audit_events(application_id)[0].event_type == AuditEventType.APPLICATION_STARTED
    )
    assert repo.list_check_runs(application_id)[0].check_type_code == CheckTypeCode.KYC
    assert repo.get_manual_review_case(application_id) is not None
