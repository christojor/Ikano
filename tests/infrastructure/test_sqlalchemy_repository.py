"""
SQLAlchemy repository integration tests.

These tests run against a real PostgreSQL database (migrated via Alembic).
They are skipped when INTEGRATION_TESTS != "1" so that unit-test runs remain
fast and DB-free.

To run locally:
    INTEGRATION_TESTS=1 pytest tests/infrastructure/test_sqlalchemy_repository.py -v
"""

import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.domain.onboarding import (
    ActorType,
    ApplicationRecord,
    ApplicationStatus,
    ApplicationStepRecord,
    AuditEvent,
    AuditEventType,
    CheckBusinessResultCode,
    CheckRunRecord,
    CheckTypeCode,
    CountryCode,
    ManualReviewCaseRecord,
    ManualReviewStatus,
    PartyTypeCode,
    StepStatusCode,
)
from app.infrastructure.config import settings
from app.infrastructure.repositories.sqlalchemy_onboarding_repository import (
    SQLAlchemyOnboardingRepository,
)

integration = pytest.mark.skipif(
    os.environ.get("INTEGRATION_TESTS") != "1",
    reason="Set INTEGRATION_TESTS=1 to run integration tests against a real DB",
)


@pytest.fixture(scope="module")
def db_session():
    engine = create_engine(settings.sqlalchemy_database_uri, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    session = factory()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def repo(db_session):
    return SQLAlchemyOnboardingRepository(session=db_session)


# ---------------------------------------------------------------------------
# Flow queries
# ---------------------------------------------------------------------------


@integration
def test_get_active_flow_se_private(repo):
    flow = repo.get_active_flow(CountryCode.SE, PartyTypeCode.PRIVATE)
    assert flow is not None
    assert flow.country_code == CountryCode.SE
    assert flow.party_type_code == PartyTypeCode.PRIVATE
    assert len(flow.steps) == 7


@integration
def test_get_active_flow_pl_business(repo):
    flow = repo.get_active_flow(CountryCode.PL, PartyTypeCode.BUSINESS)
    assert flow is not None
    assert flow.country_code == CountryCode.PL
    assert flow.party_type_code == PartyTypeCode.BUSINESS


@integration
def test_get_flow_by_id_roundtrip(repo):
    flow = repo.get_active_flow(CountryCode.SE, PartyTypeCode.PRIVATE)
    assert flow is not None
    loaded = repo.get_flow_by_id(flow.flow_id)
    assert loaded is not None
    assert loaded.flow_id == flow.flow_id
    assert loaded.country_code == CountryCode.SE


# ---------------------------------------------------------------------------
# Application CRUD
# ---------------------------------------------------------------------------


@integration
def test_create_and_get_application(repo):
    flow = repo.get_active_flow(CountryCode.SE, PartyTypeCode.PRIVATE)
    assert flow is not None
    now = datetime.now(UTC)
    application_id = repo.next_application_id()

    app = ApplicationRecord(
        application_id=application_id,
        public_reference=f"TEST-{application_id:06d}",
        country_code=CountryCode.SE,
        party_type_code=PartyTypeCode.PRIVATE,
        flow_id=flow.flow_id,
        current_step_order=1,
        current_step_code="COLLECT_PRIVATE_PROFILE",
        status=ApplicationStatus.IN_PROGRESS,
        created_at=now,
    )

    created = repo.create_application(app)
    assert created.application_id == application_id

    loaded = repo.get_application(application_id)
    assert loaded is not None
    assert loaded.public_reference == f"TEST-{application_id:06d}"
    assert loaded.country_code == CountryCode.SE
    assert loaded.status == ApplicationStatus.IN_PROGRESS


@integration
def test_update_application_status(repo):
    flow = repo.get_active_flow(CountryCode.ES, PartyTypeCode.PRIVATE)
    assert flow is not None
    now = datetime.now(UTC)
    application_id = repo.next_application_id()

    app = ApplicationRecord(
        application_id=application_id,
        public_reference=f"TEST-{application_id:06d}",
        country_code=CountryCode.ES,
        party_type_code=PartyTypeCode.PRIVATE,
        flow_id=flow.flow_id,
        current_step_order=1,
        current_step_code="COLLECT_PRIVATE_PROFILE",
        status=ApplicationStatus.IN_PROGRESS,
        created_at=now,
    )
    repo.create_application(app)

    app.status = ApplicationStatus.APPROVED
    app.submitted_at = now
    repo.update_application(app)

    loaded = repo.get_application(application_id)
    assert loaded is not None
    assert loaded.status == ApplicationStatus.APPROVED


# ---------------------------------------------------------------------------
# Audit events
# ---------------------------------------------------------------------------


@integration
def test_append_and_list_audit_events(repo):
    flow = repo.get_active_flow(CountryCode.SE, PartyTypeCode.PRIVATE)
    assert flow is not None
    now = datetime.now(UTC)
    application_id = repo.next_application_id()

    # Create application record to satisfy FK constraint
    app = ApplicationRecord(
        application_id=application_id,
        public_reference=f"TEST-{application_id:06d}",
        country_code=CountryCode.SE,
        party_type_code=PartyTypeCode.PRIVATE,
        flow_id=flow.flow_id,
        current_step_order=1,
        current_step_code="COLLECT_PRIVATE_PROFILE",
        status=ApplicationStatus.IN_PROGRESS,
        created_at=now,
    )
    repo.create_application(app)

    repo.append_audit_event(
        AuditEvent(
            application_id=application_id,
            event_type=AuditEventType.APPLICATION_STARTED,
            event_timestamp=now,
            actor_type=ActorType.SYSTEM,
            actor_id="integration-test",
            correlation_id=f"TEST-{application_id:06d}",
            metadata={"step_code": "COLLECT_PRIVATE_PROFILE"},
        )
    )

    events = repo.list_audit_events(application_id)
    assert len(events) == 1
    assert events[0].event_type == AuditEventType.APPLICATION_STARTED
    assert events[0].actor_type == ActorType.SYSTEM


# ---------------------------------------------------------------------------
# Check runs
# ---------------------------------------------------------------------------


@integration
def test_append_and_list_check_runs(repo):
    flow = repo.get_active_flow(CountryCode.SE, PartyTypeCode.PRIVATE)
    assert flow is not None
    now = datetime.now(UTC)
    application_id = repo.next_application_id()
    check_run_id = repo.next_check_run_id()

    # Create application record to satisfy FK constraint
    app = ApplicationRecord(
        application_id=application_id,
        public_reference=f"TEST-{application_id:06d}",
        country_code=CountryCode.SE,
        party_type_code=PartyTypeCode.PRIVATE,
        flow_id=flow.flow_id,
        current_step_order=1,
        current_step_code="COLLECT_PRIVATE_PROFILE",
        status=ApplicationStatus.IN_PROGRESS,
        created_at=now,
    )
    repo.create_application(app)

    repo.append_check_run(
        CheckRunRecord(
            check_run_id=check_run_id,
            application_id=application_id,
            check_type_code=CheckTypeCode.KYC,
            check_business_result_code=CheckBusinessResultCode.PASS,
            correlation_id=f"TEST-{application_id:06d}",
            input_fingerprint="PASS",
            created_at=now,
        )
    )

    runs = repo.list_check_runs(application_id)
    assert len(runs) == 1
    assert runs[0].check_type_code == CheckTypeCode.KYC
    assert runs[0].check_business_result_code == CheckBusinessResultCode.PASS


# ---------------------------------------------------------------------------
# Manual review cases
# ---------------------------------------------------------------------------


@integration
def test_create_and_get_manual_review_case(repo):
    flow = repo.get_active_flow(CountryCode.SE, PartyTypeCode.PRIVATE)
    assert flow is not None
    now = datetime.now(UTC)
    application_id = repo.next_application_id()
    review_id = repo.next_manual_review_case_id()

    # Create application record to satisfy FK constraint
    app = ApplicationRecord(
        application_id=application_id,
        public_reference=f"TEST-{application_id:06d}",
        country_code=CountryCode.SE,
        party_type_code=PartyTypeCode.PRIVATE,
        flow_id=flow.flow_id,
        current_step_order=1,
        current_step_code="COLLECT_PRIVATE_PROFILE",
        status=ApplicationStatus.IN_PROGRESS,
        created_at=now,
    )
    repo.create_application(app)

    repo.create_manual_review_case(
        ManualReviewCaseRecord(
            manual_review_case_id=review_id,
            application_id=application_id,
            review_status=ManualReviewStatus.OPEN,
            opened_at=now,
        )
    )

    loaded = repo.get_manual_review_case(application_id)
    assert loaded is not None
    assert loaded.review_status == ManualReviewStatus.OPEN
    assert loaded.application_id == application_id


@integration
def test_append_and_list_application_steps(repo):
    flow = repo.get_active_flow(CountryCode.SE, PartyTypeCode.PRIVATE)
    assert flow is not None
    now = datetime.now(UTC)
    application_id = repo.next_application_id()
    step_id = repo.next_application_step_id()

    # Create application record to satisfy FK constraint
    app = ApplicationRecord(
        application_id=application_id,
        public_reference=f"TEST-{application_id:06d}",
        country_code=CountryCode.SE,
        party_type_code=PartyTypeCode.PRIVATE,
        flow_id=flow.flow_id,
        current_step_order=1,
        current_step_code="COLLECT_PRIVATE_PROFILE",
        status=ApplicationStatus.IN_PROGRESS,
        created_at=now,
    )
    repo.create_application(app)

    repo.append_application_step(
        ApplicationStepRecord(
            application_step_id=step_id,
            application_id=application_id,
            step_code="COLLECT_SE_IDENTITY",
            step_order=1,
            step_status_code=StepStatusCode.COMPLETED,
            payload_snapshot={"identity_number": "199001019999"},
            completed_at=now,
        )
    )

    loaded = repo.list_application_steps(application_id)
    assert len(loaded) == 1
    assert loaded[0].step_status_code == StepStatusCode.COMPLETED
