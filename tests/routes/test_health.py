"""Health endpoint tests."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_ok():
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_returns_json_content_type():
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]
