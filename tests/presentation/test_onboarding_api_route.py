from fastapi.testclient import TestClient


def _payload_for_step(step_code: str, scenario: str = "PASS") -> dict[str, str]:
    payload = {"scenario": scenario}

    if step_code in {"COLLECT_SE_IDENTITY", "COLLECT_ES_DNI_NIE", "COLLECT_PL_PESEL"}:
        payload["identity_number"] = "44051401458" if step_code == "COLLECT_PL_PESEL" else "199001019999"
    elif step_code in {"CONFIRM_SE_CONTACT", "CONFIRM_ES_CONTACT", "CONFIRM_PL_CONTACT"}:
        payload["email"] = "applicant@example.com"
    elif step_code in {"COLLECT_SE_AFFORD", "COLLECT_ES_AFFORD", "COLLECT_PL_AFFORD"}:
        payload["monthly_income"] = "45000"
    elif step_code in {"RUN_SE_CREDIT", "RUN_ES_CREDIT", "RUN_PL_BIK"}:
        payload["monthly_income"] = "45000"
        payload["monthly_expenses"] = "15000"
    elif step_code in {"REVIEW_SE_SUBMIT", "REVIEW_ES_SUBMIT", "REVIEW_PL_SUBMIT"}:
        payload["accept_terms"] = "true"
    elif step_code == "COLLECT_BUSINESS_PROFILE":
        payload["organization_number"] = "556677-8899"

    return payload


def test_start_onboarding_application_route_returns_created(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/onboarding/start",
        json={"country_code": "SE", "party_type_code": "PRIVATE"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["country_code"] == "SE"
    assert payload["party_type_code"] == "PRIVATE"
    assert payload["status"] == "IN_PROGRESS"
    assert payload["current_step_code"] == "COLLECT_SE_IDENTITY"


def test_advance_onboarding_application_route_reaches_approved(api_client: TestClient) -> None:
    start_response = api_client.post(
        "/api/onboarding/start",
        json={"country_code": "SE", "party_type_code": "PRIVATE"},
    )
    application_id = start_response.json()["application_id"]

    response = start_response
    for _ in range(7):
        current_step_code = response.json()["current_step_code"]
        response = api_client.post(
            f"/api/onboarding/{application_id}/advance",
            json=_payload_for_step(current_step_code, "PASS"),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "APPROVED"
    assert payload["submitted_at"] is not None


def test_advance_onboarding_rejects_invalid_payload_for_current_step(api_client: TestClient) -> None:
    start_response = api_client.post(
        "/api/onboarding/start",
        json={"country_code": "SE", "party_type_code": "PRIVATE"},
    )
    application_id = start_response.json()["application_id"]

    response = api_client.post(
        f"/api/onboarding/{application_id}/advance",
        json={"scenario": "PASS"},
    )

    assert response.status_code == 400
    assert "identity_number is required" in response.json()["detail"]
