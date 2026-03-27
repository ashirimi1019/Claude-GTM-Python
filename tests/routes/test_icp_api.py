"""ICP API route tests."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


class TestGetIcpProfile:
    def test_returns_404_when_campaign_not_found(self):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        with patch("app.routes.icp.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.get("/api/campaigns/fake-id/icp-profile")
            assert resp.status_code == 404

    def test_returns_404_when_icp_profile_is_null(self):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "c1", "icp_profile": None}]
        )

        with patch("app.routes.icp.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.get("/api/campaigns/c1/icp-profile")
            assert resp.status_code == 404

    def test_returns_icp_profile(self):
        profile = {"version": 1, "mode": "basic"}
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "c1", "icp_profile": profile}]
        )

        with patch("app.routes.icp.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.get("/api/campaigns/c1/icp-profile")
            assert resp.status_code == 200
            data = resp.json()
            assert data["icp_profile"] == profile
            assert data["campaign_id"] == "c1"


class TestSaveIcpProfile:
    def test_validates_profile_before_saving(self):
        # Invalid profile (missing version)
        with patch("app.routes.icp.get_supabase_client", return_value=MagicMock()):
            client = _client()
            resp = client.post("/api/campaigns/c1/icp-profile", json={"mode": "basic"})
            assert resp.status_code == 422

    def test_saves_valid_profile(self):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "c1"}]
        )
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "c1"}]
        )

        valid_profile = {"version": 1, "mode": "basic"}
        with patch("app.routes.icp.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.post("/api/campaigns/c1/icp-profile", json=valid_profile)
            assert resp.status_code == 200
            data = resp.json()
            assert data["saved"] is True


class TestIcpPreview:
    def test_returns_summary_with_profile_only(self):
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

    def test_returns_empty_when_no_profile(self):
        client = _client()
        resp = client.post("/api/icp/preview", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"] == {"total_companies": 0, "qualified": 0}
