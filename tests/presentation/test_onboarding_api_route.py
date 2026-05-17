from fastapi.testclient import TestClient


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
    assert payload["current_step_code"] == "COLLECT_PRIVATE_PROFILE"


def test_advance_onboarding_application_route_reaches_approved(api_client: TestClient) -> None:
    start_response = api_client.post(
        "/api/onboarding/start",
        json={"country_code": "SE", "party_type_code": "PRIVATE"},
    )
    application_id = start_response.json()["application_id"]

    response = start_response
    for _ in range(4):
        response = api_client.post(
            f"/api/onboarding/{application_id}/advance",
            json={"scenario": "PASS"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "APPROVED"
    assert payload["submitted_at"] is not None
