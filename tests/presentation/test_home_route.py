from fastapi.testclient import TestClient


def test_home_route_renders_html(api_client: TestClient) -> None:
    response = api_client.get("/")

    assert response.status_code == 200
    assert "Welcome to Ikano Bank" in response.text
    assert "Start Application" in response.text
