"""Safety routes tests — health monitor, variants, artifacts, cron."""

import os

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app

AGENT_SECRET = "test-agent-secret"
AUTH_HEADERS = {"x-agent-secret": AGENT_SECRET}


def _client():
    os.environ["AGENT_INTERNAL_SECRET"] = AGENT_SECRET
    get_settings.cache_clear()
    return TestClient(create_app())


class TestHealthMonitor:
    def test_health_monitor_returns_results(self):
        client = _client()
        resp = client.post("/api/agents/health", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "sequences_checked" in data
        assert "sequences_paused" in data


class TestVariants:
    def test_list_pending_returns_empty(self):
        client = _client()
        resp = client.get("/api/variants/pending")
        assert resp.status_code == 200
        assert resp.json()["pending"] == []

    def test_approve_variant(self):
        client = _client()
        resp = client.post("/api/variants/test-id/approve?approved=true&reason=looks+good")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "approved"

    def test_reject_variant(self):
        client = _client()
        resp = client.post("/api/variants/test-id/approve?approved=false&reason=too+salesy")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "rejected"


class TestArtifacts:
    def test_list_artifacts_empty(self):
        client = _client()
        resp = client.get("/api/artifacts?offer_slug=nonexistent")
        assert resp.status_code == 200
        assert resp.json()["artifacts"] == []

    def test_list_artifacts_with_real_offer(self):
        client = _client()
        resp = client.get("/api/artifacts?offer_slug=talent-as-a-service-us")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["artifacts"]) > 0

    def test_get_artifact_not_found(self):
        client = _client()
        resp = client.get("/api/artifacts/nonexistent/file.md")
        assert resp.status_code == 404


class TestCron:
    def test_cleanup_stale_runs_with_valid_secret(self):
        client = _client()
        resp = client.post(
            "/api/cron/cleanup-stale-runs",
            headers={"x-agent-secret": "test-agent-secret"},
        )
        assert resp.status_code == 200
        assert resp.json()["cleaned"] == 0

    def test_cleanup_stale_runs_rejects_missing_secret(self):
        client = _client()
        resp = client.post("/api/cron/cleanup-stale-runs")
        assert resp.status_code == 422  # missing required header

    def test_cleanup_stale_runs_rejects_wrong_secret(self):
        client = _client()
        resp = client.post(
            "/api/cron/cleanup-stale-runs",
            headers={"x-agent-secret": "wrong-secret"},
        )
        assert resp.status_code == 403
