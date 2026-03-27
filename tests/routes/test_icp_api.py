"""ICP API route tests."""

from fastapi.testclient import TestClient

from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_get_icp_profile_returns_404():
    client = _client()
    resp = client.get("/api/campaigns/fake-id/icp-profile")
    assert resp.status_code == 404


def test_icp_preview_returns_summary():
    client = _client()
    resp = client.post("/api/icp/preview", json={
        "icp_profile": {"min_employees": 50},
        "source": "inline",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "effective_config" in data
    assert data["effective_config"] == {"min_employees": 50}
