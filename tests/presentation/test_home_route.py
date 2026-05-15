from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_home_route_renders_html() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Ikano Python Developer Work Sample" in response.text
