"""Skills API route tests."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


@patch("app.routes.skills.run_skill_task", create=True)
def test_run_skill_returns_task_id(mock_task):
    """POST /api/skills/run dispatches Celery task and returns its ID."""
    fake_result = MagicMock()
    fake_result.id = "celery-task-id-123"

    # Patch the import inside the route handler
    with patch("workers.skill_tasks.run_skill_task") as mock_inner:
        mock_inner.delay.return_value = fake_result
        client = _client()
        resp = client.post("/api/skills/run", json={
            "skill_id": 1,
            "offer_slug": "test-offer",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["task_id"] == "celery-task-id-123"
    assert data["status"] == "queued"
    mock_inner.delay.assert_called_once_with(
        skill_id=1,
        offer_slug="test-offer",
        campaign_slug=None,
        config=None,
    )


@patch("workers.skill_tasks.run_skill_task")
def test_run_skill_returns_503_when_redis_down(mock_task):
    """POST /api/skills/run returns 503 if Celery dispatch fails."""
    mock_task.delay.side_effect = ConnectionError("Redis unavailable")
    client = _client()
    resp = client.post("/api/skills/run", json={
        "skill_id": 1,
        "offer_slug": "test-offer",
    })
    assert resp.status_code == 503
    data = resp.json()
    assert data["error"] == "QUEUE_UNAVAILABLE"


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


@patch("app.routes.skills.sse_skill_stream")
def test_stream_returns_sse(mock_sse):
    """GET /api/skills/stream calls sse_skill_stream with correct channel."""
    from sse_starlette.sse import EventSourceResponse

    # Create a mock EventSourceResponse-like streaming response
    async def fake_generator():
        yield {"data": '{"status": "connected"}'}

    mock_sse.return_value = EventSourceResponse(fake_generator())

    client = _client()
    resp = client.get("/api/skills/stream", params={
        "offer": "test-offer",
        "campaign": "test-campaign",
        "skill": 1,
    })
    assert resp.status_code == 200
    mock_sse.assert_called_once()
    # Verify the channel name format
    call_args = mock_sse.call_args
    assert call_args[0][0] == "skill-run:test-offer:test-campaign:1"
