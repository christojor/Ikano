from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

# Ensure imports work when script is launched directly from VS Code debugpy.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.application.services.onboarding_service import OnboardingService  # noqa: E402
from app.infrastructure.repositories.in_memory_onboarding_repository import (  # noqa: E402
    InMemoryOnboardingRepository,
)
from app.main import create_app  # noqa: E402
from app.presentation.dependencies import get_onboarding_service  # noqa: E402


def checkpoint(*, step_no: int, title: str, what: str, how: str, why: str) -> None:
    print("\n" + "=" * 88)
    print(f"STEP {step_no}: {title}")
    print("-" * 88)
    print(f"WHAT: {what}")
    print(f"HOW:  {how}")
    print(f"WHY:  {why}")
    input("\nPress Enter to continue to the next step... ")


def summarize_response(label: str, response_json: dict[str, Any]) -> None:
    print(f"\n{label}")
    print("-" * len(label))
    for key in (
        "application_id",
        "public_reference",
        "country_code",
        "party_type_code",
        "status",
        "current_step_code",
        "current_step_order",
        "submitted_at",
    ):
        if key in response_json:
            print(f"{key}: {response_json[key]}")


def post_advance(client: TestClient, application_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post(f"/api/onboarding/{application_id}/advance", json=payload)
    response.raise_for_status()
    return response.json()


def main() -> None:
    # Keep one shared service instance so repository state is preserved across requests.
    repository = InMemoryOnboardingRepository()
    service = OnboardingService(repository=repository)

    app = create_app()
    app.dependency_overrides[get_onboarding_service] = lambda: service
    client = TestClient(app)

    checkpoint(
        step_no=0,
        title="Debug Session Setup",
        what=(
            "Start a controlled end-to-end walkthrough for a fictitious but realistic use case: "
            "Sweden + private customer, with borderline affordability that escalates to manual review."
        ),
        how=(
            "A FastAPI TestClient sends real HTTP requests through routes, dependency injection, "
            "application services, progression logic, deterministic checks, decisioning, and audit persistence."
        ),
        why=(
            "This gives a deterministic, repeatable, debugger-friendly session that mirrors production data flow "
            "without external systems."
        ),
    )

    checkpoint(
        step_no=1,
        title="Start Application (Flow Resolution)",
        what=(
            "Create a new onboarding application and resolve one of six flows from country + account type."
        ),
        how=(
            "POST /api/onboarding/start with country_code=SE and party_type_code=PRIVATE. "
            "Route delegates to OnboardingService.start_application()."
        ),
        why=(
            "This demonstrates adaptable flow selection and initialization of application state."
        ),
    )
    start_res = client.post(
        "/api/onboarding/start",
        json={"country_code": "SE", "party_type_code": "PRIVATE"},
    )
    start_res.raise_for_status()
    app_state = start_res.json()
    application_id = app_state["application_id"]
    summarize_response("Application after start", app_state)

    checkpoint(
        step_no=2,
        title="Step 1 - Collect Identity",
        what="Persist user input for identity collection step.",
        how=(
            "POST /api/onboarding/{id}/advance with identity_number. "
            "StepPayloadValidationService validates required field format for COLLECT_SE_IDENTITY."
        ),
        why=(
            "Shows step-specific validation and progression without external check execution yet."
        ),
    )
    app_state = post_advance(
        client,
        application_id,
        {"identity_number": "199001019999"},
    )
    summarize_response("Application after step 1", app_state)

    checkpoint(
        step_no=3,
        title="Step 2 - Identity Check (KYC)",
        what="Execute deterministic KYC check and persist check result + audit event.",
        how=(
            "Advance RUN_SE_BANKID step with scenario=PASS and technical_scenario=OK. "
            "OnboardingService calls DeterministicCheckService and stores check_run."
        ),
        why=(
            "Shows integration boundary behavior and deterministic mocking strategy."
        ),
    )
    app_state = post_advance(
        client,
        application_id,
        {"scenario": "PASS", "technical_scenario": "OK"},
    )
    summarize_response("Application after step 2", app_state)

    checkpoint(
        step_no=4,
        title="Step 3 - Contact + Address Check",
        what="Validate contact payload and execute address verification check.",
        how=(
            "Advance CONFIRM_SE_CONTACT with email plus scenario=PASS. "
            "Validation + check execution + audit append happen in one transaction boundary."
        ),
        why=(
            "Demonstrates combined payload validation and check orchestration on a single step."
        ),
    )
    app_state = post_advance(
        client,
        application_id,
        {
            "email": "anna.svensson@example.com",
            "scenario": "PASS",
            "technical_scenario": "OK",
        },
    )
    summarize_response("Application after step 3", app_state)

    checkpoint(
        step_no=5,
        title="Step 4 - Sanctions/PEP Check",
        what="Run sanctions screening check.",
        how=(
            "Advance CAPTURE_SE_CONSENT with scenario=PASS. "
            "Service appends STEP_COMPLETED and CHECK_COMPLETED audit entries."
        ),
        why=(
            "Shows regulatory control point and audit trail transparency."
        ),
    )
    app_state = post_advance(
        client,
        application_id,
        {"scenario": "PASS", "technical_scenario": "OK"},
    )
    summarize_response("Application after step 4", app_state)

    checkpoint(
        step_no=6,
        title="Step 5 - Affordability Inputs",
        what="Capture affordability input data without running a check yet.",
        how=(
            "Advance COLLECT_SE_AFFORD with monthly_income. "
            "StepPayloadValidationService enforces positive numeric input."
        ),
        why=(
            "Separates data capture from decision execution; improves explainability and testability."
        ),
    )
    app_state = post_advance(
        client,
        application_id,
        {"monthly_income": "25000"},
    )
    summarize_response("Application after step 5", app_state)

    checkpoint(
        step_no=7,
        title="Step 6 - Credit + Affordability Decision",
        what=(
            "Apply affordability rules and execute credit check; this scenario intentionally results in MANUAL_REVIEW."
        ),
        how=(
            "Advance RUN_SE_CREDIT with monthly_income=25000 and monthly_expenses=17000. "
            "OnboardingService._apply_credit_affordability_rules computes disposable income=8000 and sets scenario=MANUAL_REVIEW."
        ),
        why=(
            "Demonstrates business-rule transformation before integration check and explainable non-happy-path outcomes."
        ),
    )
    app_state = post_advance(
        client,
        application_id,
        {
            "monthly_income": "25000",
            "monthly_expenses": "17000",
            "technical_scenario": "OK",
        },
    )
    summarize_response("Application after step 6", app_state)

    checkpoint(
        step_no=8,
        title="Step 7 - Final Submit and Decision Finalization",
        what="Finalize onboarding and compute final application outcome from accumulated checks.",
        how=(
            "Advance REVIEW_SE_SUBMIT with accept_terms=true. "
            "DecisionService evaluates all check_runs: no FAIL, but at least one MANUAL_REVIEW => UNDER_REVIEW."
        ),
        why=(
            "Shows deterministic final decisioning and when manual review case creation is triggered."
        ),
    )
    app_state = post_advance(
        client,
        application_id,
        {"accept_terms": "true"},
    )
    summarize_response("Application after final submit", app_state)

    checkpoint(
        step_no=9,
        title="Inspect End-to-End Artifacts",
        what="Inspect generated trace artifacts: audit events, check runs, step trail, manual review case.",
        how=(
            "GET /api/onboarding/{id}/audit-events, /check-runs, /steps, /manual-review. "
            "Print event counts and terminal status."
        ),
        why=(
            "This closes the loop and proves observability, supportability, and compliance traceability."
        ),
    )

    audit_events = client.get(f"/api/onboarding/{application_id}/audit-events")
    check_runs = client.get(f"/api/onboarding/{application_id}/check-runs")
    steps = client.get(f"/api/onboarding/{application_id}/steps")
    manual_review = client.get(f"/api/onboarding/{application_id}/manual-review")

    audit_events.raise_for_status()
    check_runs.raise_for_status()
    steps.raise_for_status()
    manual_review.raise_for_status()

    print("\nFinal artifact summary")
    print("----------------------")
    print(f"Audit events: {len(audit_events.json())}")
    print(f"Check runs: {len(check_runs.json())}")
    print(f"Completed steps: {len(steps.json())}")
    print(f"Manual review case: {manual_review.json()}")

    print("\nWalkthrough complete. Suggested debugger breakpoints:")
    print("1) app/presentation/web/routes.py -> start_onboarding() and advance_onboarding()")
    print("2) app/application/services/onboarding_service.py -> start_application(), advance_step()")
    print("3) app/application/services/step_payload_validation_service.py -> validate()")
    print("4) app/application/services/deterministic_check_service.py -> evaluate()")
    print("5) app/application/services/decision_service.py -> decide()")
    print("6) app/application/services/audit_trail_service.py -> _append()")
    print("7) app/application/services/application_progression_service.py -> move_to_next_step()")


if __name__ == "__main__":
    main()
