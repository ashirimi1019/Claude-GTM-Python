"""Skills API route tests."""

from fastapi.testclient import TestClient

from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_run_skill_returns_task_id():
    client = _client()
    resp = client.post("/api/skills/run", json={
        "skill_id": 1,
        "offer_slug": "test-offer",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data
    assert data["status"] == "queued"


def test_status_returns_dict():
    client = _client()
    resp = client.get("/api/skills/status", params={
        "offer_slug": "test-offer",
        "skill_id": 1,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["skill_id"] == 1
    assert isinstance(data["outputs"], dict)


def test_run_summary_returns_404_when_missing():
    client = _client()
    resp = client.get("/api/skills/run-summary", params={
        "offer": "nonexistent",
        "campaign": "nonexistent",
    })
    assert resp.status_code == 404


def test_stream_returns_sse():
    client = _client()
    resp = client.get("/api/skills/stream", params={
        "offer": "test-offer",
        "campaign": "test-campaign",
        "skill": 1,
    })
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    assert "data:" in resp.text
