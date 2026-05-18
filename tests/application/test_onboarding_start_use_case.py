import pytest

from app.application.domain.exceptions import UnsupportedCountryCodeError
from app.application.domain.onboarding import ApplicationStatus
from app.application.services.onboarding_service import OnboardingService
from app.infrastructure.repositories.in_memory_onboarding_repository import (
    InMemoryOnboardingRepository,
)


def _payload_for_step(
    step_code: str,
    scenario: str = "PASS",
    technical_scenario: str = "OK",
) -> dict[str, str]:
    payload = {"scenario": scenario, "technical_scenario": technical_scenario}

    step_payloads: dict[str, dict[str, str]] = {
        "COLLECT_SE_IDENTITY": {"identity_number": "199001019999"},
        "COLLECT_ES_DNI_NIE": {"identity_number": "199001019999"},
        "COLLECT_PL_PESEL": {"identity_number": "44051401458"},
        "CONFIRM_SE_CONTACT": {"email": "applicant@example.com"},
        "CONFIRM_ES_CONTACT": {"email": "applicant@example.com"},
        "CONFIRM_PL_CONTACT": {"email": "applicant@example.com"},
        "COLLECT_SE_AFFORD": {"monthly_income": "45000"},
        "COLLECT_ES_AFFORD": {"monthly_income": "45000"},
        "COLLECT_PL_AFFORD": {"monthly_income": "45000"},
        "RUN_SE_CREDIT": {"monthly_income": "45000", "monthly_expenses": "15000"},
        "RUN_ES_CREDIT": {"monthly_income": "45000", "monthly_expenses": "15000"},
        "RUN_PL_BIK": {"monthly_income": "45000", "monthly_expenses": "15000"},
        "COLLECT_BUSINESS_PROFILE": {"organization_number": "556677-8899"},
        "VERIFY_BUSINESS_REPRESENTATIVE": {"representative_identity": "197905059999"},
        "CAPTURE_BUSINESS_OWNERSHIP": {"ubo_identifier": "UBO-778899"},
        "RUN_BUSINESS_CREDIT": {"monthly_income": "45000", "monthly_expenses": "15000"},
        "REVIEW_SE_SUBMIT": {"accept_terms": "true"},
        "REVIEW_ES_SUBMIT": {"accept_terms": "true"},
        "REVIEW_PL_SUBMIT": {"accept_terms": "true"},
        "REVIEW_BUSINESS_SUBMIT": {
            "accept_terms": "true",
            "bank_iban": "SE3550000000054910000003",
        },
    }
    payload.update(step_payloads.get(step_code, {}))

    return payload


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
        payload=_payload_for_step(application.current_step_code, "PASS"),
    )

    assert updated.current_step_order == 2
    assert updated.current_step_code == "RUN_SE_BANKID"
    assert updated.status == ApplicationStatus.IN_PROGRESS


def test_advance_step_completes_happy_path_with_approval(onboarding_service: OnboardingService) -> None:
    application = onboarding_service.start_application(country_code="SE", party_type_code="PRIVATE")
    flow = onboarding_service.get_flow_for_application(application.application_id)

    updated = application
    for _ in range(len(flow.steps)):
        updated = onboarding_service.advance_step(
            application_id=updated.application_id,
            payload=_payload_for_step(updated.current_step_code, "PASS"),
        )

    assert updated.status == ApplicationStatus.APPROVED
    assert updated.submitted_at is not None


def test_manual_review_outcome_creates_manual_review_case(
    onboarding_service: OnboardingService,
) -> None:
    application = onboarding_service.start_application(country_code="ES", party_type_code="PRIVATE")
    flow = onboarding_service.get_flow_for_application(application.application_id)

    updated = application
    for _ in range(len(flow.steps)):
        updated = onboarding_service.advance_step(
            application_id=updated.application_id,
            payload=_payload_for_step(updated.current_step_code, "MANUAL_REVIEW"),
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
    flow = onboarding_service.get_flow_for_application(application.application_id)

    updated = application
    for _ in range(len(flow.steps)):
        updated = onboarding_service.advance_step(
            application_id=updated.application_id,
            payload=_payload_for_step(updated.current_step_code, "FAIL"),
        )

    case = onboarding_service.get_manual_review_case(application_id=updated.application_id)

    assert updated.status == ApplicationStatus.REJECTED
    assert case is None


def test_check_runs_are_deterministic_from_payload_scenario(
    onboarding_service: OnboardingService,
) -> None:
    app_manual = onboarding_service.start_application(country_code="SE", party_type_code="PRIVATE")
    app_pass = onboarding_service.start_application(country_code="SE", party_type_code="PRIVATE")
    flow = onboarding_service.get_flow_for_application(app_manual.application_id)

    for _ in range(len(flow.steps)):
        app_manual = onboarding_service.advance_step(
            application_id=app_manual.application_id,
            payload=_payload_for_step(app_manual.current_step_code, "MANUAL_REVIEW"),
        )
        app_pass = onboarding_service.advance_step(
            application_id=app_pass.application_id,
            payload=_payload_for_step(app_pass.current_step_code, "PASS"),
        )

    check_runs_manual = onboarding_service.get_check_runs(application_id=app_manual.application_id)
    check_runs_pass = onboarding_service.get_check_runs(application_id=app_pass.application_id)

    assert check_runs_manual
    assert check_runs_pass
    assert check_runs_manual[0].check_business_result_code == "MANUAL_REVIEW"
    assert all(check.check_business_result_code == "PASS" for check in check_runs_pass)


def test_credit_step_uses_affordability_inputs_for_decision(
    onboarding_service: OnboardingService,
) -> None:
    application = onboarding_service.start_application(country_code="SE", party_type_code="PRIVATE")

    updated = application
    for _ in range(5):
        updated = onboarding_service.advance_step(
            application_id=updated.application_id,
            payload=_payload_for_step(updated.current_step_code, "PASS"),
        )

    # At RUN_SE_CREDIT: force negative disposable income => FAIL
    updated = onboarding_service.advance_step(
        application_id=updated.application_id,
        payload={
            "scenario": "PASS",
            "monthly_income": "1000",
            "monthly_expenses": "2500",
        },
    )

    # Final review step then decision
    updated = onboarding_service.advance_step(
        application_id=updated.application_id,
        payload={"scenario": "PASS", "accept_terms": "true"},
    )

    assert updated.status == ApplicationStatus.REJECTED


def test_timeout_and_error_paths_are_persisted_in_audit_metadata(
    onboarding_service: OnboardingService,
) -> None:
    application = onboarding_service.start_application(country_code="SE", party_type_code="PRIVATE")

    # Step 1 has no check.
    updated = onboarding_service.advance_step(
        application_id=application.application_id,
        payload=_payload_for_step(application.current_step_code, scenario="PASS"),
    )
    # Step 2 (KYC) timeout path.
    updated = onboarding_service.advance_step(
        application_id=updated.application_id,
        payload=_payload_for_step(updated.current_step_code, scenario="PASS", technical_scenario="TIMEOUT"),
    )
    # Step 3 (ADDRESS) pass path.
    updated = onboarding_service.advance_step(
        application_id=updated.application_id,
        payload=_payload_for_step(updated.current_step_code, scenario="PASS"),
    )
    # Step 4 (SANCTIONS) error path.
    updated = onboarding_service.advance_step(
        application_id=updated.application_id,
        payload=_payload_for_step(updated.current_step_code, scenario="PASS", technical_scenario="ERROR"),
    )

    events = onboarding_service.get_audit_events(application_id=updated.application_id)
    check_events = [event for event in events if event.event_type == "CHECK_COMPLETED"]

    assert len(check_events) == 3
    assert check_events[0].metadata["check_technical_result_code"] == "TIMEOUT"
    assert check_events[0].metadata["check_business_result_code"] == "MANUAL_REVIEW"
    assert check_events[1].metadata["check_technical_result_code"] == "OK"
    assert check_events[1].metadata["check_business_result_code"] == "PASS"
    assert check_events[2].metadata["check_technical_result_code"] == "ERROR"
    assert check_events[2].metadata["check_business_result_code"] == "FAIL"


def test_business_flow_has_seven_steps_and_can_approve(
    onboarding_service: OnboardingService,
) -> None:
    application = onboarding_service.start_application(country_code="SE", party_type_code="BUSINESS")
    flow = onboarding_service.get_flow_for_application(application.application_id)

    assert len(flow.steps) == 7

    updated = application
    for _ in range(len(flow.steps)):
        updated = onboarding_service.advance_step(
            application_id=updated.application_id,
            payload=_payload_for_step(updated.current_step_code, "PASS"),
        )

    assert updated.status == ApplicationStatus.APPROVED


def test_business_flow_manual_review_path_creates_case(
    onboarding_service: OnboardingService,
) -> None:
    application = onboarding_service.start_application(country_code="ES", party_type_code="BUSINESS")
    flow = onboarding_service.get_flow_for_application(application.application_id)

    updated = application
    for _ in range(len(flow.steps)):
        scenario = "MANUAL_REVIEW" if updated.current_step_code == "RUN_KYB" else "PASS"
        updated = onboarding_service.advance_step(
            application_id=updated.application_id,
            payload=_payload_for_step(updated.current_step_code, scenario),
        )

    case = onboarding_service.get_manual_review_case(application_id=updated.application_id)
    assert updated.status == ApplicationStatus.UNDER_REVIEW
    assert case is not None


def test_business_flow_rejects_when_bank_check_fails(
    onboarding_service: OnboardingService,
) -> None:
    application = onboarding_service.start_application(country_code="PL", party_type_code="BUSINESS")
    flow = onboarding_service.get_flow_for_application(application.application_id)

    updated = application
    for _ in range(len(flow.steps)):
        scenario = "FAIL" if updated.current_step_code == "REVIEW_BUSINESS_SUBMIT" else "PASS"
        updated = onboarding_service.advance_step(
            application_id=updated.application_id,
            payload=_payload_for_step(updated.current_step_code, scenario),
        )

    assert updated.status == ApplicationStatus.REJECTED


def test_application_decision_event_includes_reason_codes_and_rule_version(
    onboarding_service: OnboardingService,
) -> None:
    application = onboarding_service.start_application(country_code="SE", party_type_code="PRIVATE")
    flow = onboarding_service.get_flow_for_application(application.application_id)

    updated = application
    for _ in range(len(flow.steps)):
        updated = onboarding_service.advance_step(
            application_id=updated.application_id,
            payload=_payload_for_step(updated.current_step_code, scenario="PASS"),
        )

    events = onboarding_service.get_audit_events(application_id=updated.application_id)
    decision_events = [event for event in events if event.event_type == "APPLICATION_DECIDED"]

    assert len(decision_events) == 1
    assert decision_events[0].metadata["rule_version"] == "decision-rules/v1"
    assert decision_events[0].metadata["reason_codes"] == "ALL_CHECKS_PASSED"
    assert "explanation_json" in decision_events[0].metadata
