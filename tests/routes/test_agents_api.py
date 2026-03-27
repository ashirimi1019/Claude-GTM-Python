"""Agents API route tests."""

import os
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app

AGENT_SECRET = "test-agent-secret"
AUTH_HEADERS = {"x-agent-secret": AGENT_SECRET}


def _client() -> TestClient:
    os.environ["AGENT_INTERNAL_SECRET"] = AGENT_SECRET
    get_settings.cache_clear()
    return TestClient(create_app())


@patch("workers.agent_tasks.run_agent_pipeline")
def test_run_agents_returns_task_id(mock_task):
    """POST /api/agents/run dispatches Celery task and returns its ID."""
    fake_result = MagicMock()
    fake_result.id = "agent-celery-id-456"
    mock_task.delay.return_value = fake_result

    client = _client()
    resp = client.post("/api/agents/run", json={
        "offer_slug": "test-offer",
        "campaign_slug": "test-campaign",
    }, headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_id"] == "agent-celery-id-456"
    assert data["status"] == "queued"
    mock_task.delay.assert_called_once_with(
        offer_slug="test-offer",
        campaign_slug="test-campaign",
    )


@patch("workers.agent_tasks.run_agent_pipeline")
def test_run_agents_returns_503_when_redis_down(mock_task):
    """POST /api/agents/run returns 503 if Celery dispatch fails."""
    mock_task.delay.side_effect = ConnectionError("Redis unavailable")
    client = _client()
    resp = client.post("/api/agents/run", json={
        "offer_slug": "test-offer",
        "campaign_slug": "test-campaign",
    }, headers=AUTH_HEADERS)
    assert resp.status_code == 503
    data = resp.json()
    assert data["error"] == "QUEUE_UNAVAILABLE"


def test_get_agent_config_returns_defaults():
    client = _client()
    resp = client.get("/api/agents/config", params={"campaign_id": "abc"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["campaign_id"] == "abc"
    assert data["autonomy_level"] == "supervised"


def test_list_pending_approvals_returns_empty():
    client = _client()
    resp = client.get("/api/agents/approve", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json() == []
