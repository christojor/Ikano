from fastapi.testclient import TestClient


def _payload_for_step(step_code: str, scenario: str = "PASS") -> dict[str, str]:
    payload = {"scenario": scenario}

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
        "REVIEW_SE_SUBMIT": {"accept_terms": "true"},
        "REVIEW_ES_SUBMIT": {"accept_terms": "true"},
        "REVIEW_PL_SUBMIT": {"accept_terms": "true"},
        "COLLECT_BUSINESS_PROFILE": {"organization_number": "556677-8899"},
        "VERIFY_BUSINESS_REPRESENTATIVE": {"representative_identity": "197905059999"},
        "CAPTURE_BUSINESS_OWNERSHIP": {"ubo_identifier": "UBO-778899"},
        "RUN_BUSINESS_CREDIT": {"monthly_income": "45000", "monthly_expenses": "15000"},
        "REVIEW_BUSINESS_SUBMIT": {
            "accept_terms": "true",
            "bank_iban": "SE3550000000054910000003",
        },
    }
    payload.update(step_payloads.get(step_code, {}))

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
