from fastapi.testclient import TestClient

from app.infrastructure.config import settings


def test_home_route_renders_html(api_client: TestClient) -> None:
    response = api_client.get("/")

    assert response.status_code == 200
    assert "Welcome to Banana Bank" in response.text
    assert "Start Application" in response.text
    assert "id=\"service-status\"" in response.text
    assert "Service status: ok" in response.text


def test_home_route_hides_service_status_when_config_disabled(
    api_client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "show_home_service_status", False)

    response = api_client.get("/")

    assert response.status_code == 200
    assert "id=\"service-status\"" not in response.text
    assert "Service status: ok" not in response.text


def test_unknown_web_route_renders_not_found_page(api_client: TestClient) -> None:
    response = api_client.get("/does-not-exist")

    assert response.status_code == 404
    assert "Page Not Found" in response.text
    assert "/does-not-exist" in response.text


def test_unknown_api_route_returns_json_not_found(api_client: TestClient) -> None:
    response = api_client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
