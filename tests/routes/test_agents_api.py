"""Agents API route tests."""

from fastapi.testclient import TestClient

from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_run_agents_returns_task_id():
    client = _client()
    resp = client.post("/api/agents/run", json={
        "offer_slug": "test-offer",
        "campaign_slug": "test-campaign",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data
    assert data["status"] == "queued"


def test_get_agent_config_returns_defaults():
    client = _client()
    resp = client.get("/api/agents/config", params={"campaign_id": "abc"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["campaign_id"] == "abc"
    assert data["autonomy_level"] == "supervised"


def test_list_pending_approvals_returns_empty():
    client = _client()
    resp = client.get("/api/agents/approve")
    assert resp.status_code == 200
    assert resp.json() == []
