import pytest

from app.application.domain.exceptions import UnsupportedCountryCodeError
from app.application.domain.onboarding import ApplicationStatus
from app.application.services.onboarding_service import OnboardingService
from app.infrastructure.repositories.in_memory_onboarding_repository import (
    InMemoryOnboardingRepository,
)


@pytest.fixture
def onboarding_service() -> OnboardingService:
    repository = InMemoryOnboardingRepository()
    return OnboardingService(
        repository=repository,
    )


def test_start_application_supports_all_required_country_party_combinations(
    onboarding_service: OnboardingService,
) -> None:
    journeys = [
        ("SE", "PRIVATE"),
        ("SE", "BUSINESS"),
        ("ES", "PRIVATE"),
        ("ES", "BUSINESS"),
        ("PL", "PRIVATE"),
        ("PL", "BUSINESS"),
    ]

    started = [
        onboarding_service.start_application(country_code=country, party_type_code=party)
        for country, party in journeys
    ]

    assert len(started) == 6
    assert {app.country_code for app in started} == {"SE", "ES", "PL"}
    assert {app.party_type_code for app in started} == {"PRIVATE", "BUSINESS"}
    assert all(app.current_step_code for app in started)


def test_start_application_rejects_unknown_country(onboarding_service: OnboardingService) -> None:
    with pytest.raises(UnsupportedCountryCodeError, match="Unsupported country code"):
        onboarding_service.start_application(country_code="NO", party_type_code="PRIVATE")


def test_start_application_writes_audit_event(onboarding_service: OnboardingService) -> None:
    application = onboarding_service.start_application(country_code="SE", party_type_code="PRIVATE")

    events = onboarding_service.get_audit_events(application_id=application.application_id)

    assert events
    assert events[0].event_type == "APPLICATION_STARTED"


def test_advance_step_moves_to_next_step(onboarding_service: OnboardingService) -> None:
    application = onboarding_service.start_application(country_code="SE", party_type_code="PRIVATE")

    updated = onboarding_service.advance_step(
        application_id=application.application_id,
        payload={"scenario": "PASS"},
    )

    assert updated.current_step_order == 2
    assert updated.current_step_code == "RUN_KYC"
    assert updated.status == ApplicationStatus.IN_PROGRESS


def test_advance_step_completes_happy_path_with_approval(onboarding_service: OnboardingService) -> None:
    application = onboarding_service.start_application(country_code="SE", party_type_code="PRIVATE")

    updated = application
    for _ in range(4):
        updated = onboarding_service.advance_step(
            application_id=updated.application_id,
            payload={"scenario": "PASS"},
        )

    assert updated.status == ApplicationStatus.APPROVED
    assert updated.submitted_at is not None


def test_manual_review_outcome_creates_manual_review_case(
    onboarding_service: OnboardingService,
) -> None:
    application = onboarding_service.start_application(country_code="ES", party_type_code="PRIVATE")

    updated = application
    for _ in range(4):
        updated = onboarding_service.advance_step(
            application_id=updated.application_id,
            payload={"scenario": "MANUAL_REVIEW"},
        )

    case = onboarding_service.get_manual_review_case(application_id=updated.application_id)
    events = onboarding_service.get_audit_events(application_id=updated.application_id)

    assert updated.status == ApplicationStatus.UNDER_REVIEW
    assert case is not None
    assert case.review_status.value == "OPEN"
    assert any(event.event_type == "MANUAL_REVIEW_OPENED" for event in events)


def test_fail_outcome_rejects_application_and_does_not_open_manual_case(
    onboarding_service: OnboardingService,
) -> None:
    application = onboarding_service.start_application(country_code="PL", party_type_code="PRIVATE")

    updated = application
    for _ in range(4):
        updated = onboarding_service.advance_step(
            application_id=updated.application_id,
            payload={"scenario": "FAIL"},
        )

    case = onboarding_service.get_manual_review_case(application_id=updated.application_id)

    assert updated.status == ApplicationStatus.REJECTED
    assert case is None


def test_check_runs_are_deterministic_from_payload_scenario(
    onboarding_service: OnboardingService,
) -> None:
    app_manual = onboarding_service.start_application(country_code="SE", party_type_code="PRIVATE")
    app_pass = onboarding_service.start_application(country_code="SE", party_type_code="PRIVATE")

    for _ in range(4):
        app_manual = onboarding_service.advance_step(
            application_id=app_manual.application_id,
            payload={"scenario": "MANUAL_REVIEW"},
        )
        app_pass = onboarding_service.advance_step(
            application_id=app_pass.application_id,
            payload={"scenario": "PASS"},
        )

    check_runs_manual = onboarding_service.get_check_runs(application_id=app_manual.application_id)
    check_runs_pass = onboarding_service.get_check_runs(application_id=app_pass.application_id)

    assert check_runs_manual
    assert check_runs_pass
    assert all(check.check_business_result_code == "MANUAL_REVIEW" for check in check_runs_manual)
    assert all(check.check_business_result_code == "PASS" for check in check_runs_pass)
