"""Campaigns API route tests."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def _mock_supabase():
    """Create a mock supabase client with chainable table methods."""
    mock = MagicMock()
    return mock


class TestListCampaigns:
    def test_returns_empty_list(self):
        mock_sb = _mock_supabase()
        mock_sb.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(data=[])

        with patch("app.routes.campaigns.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.get("/api/campaigns")
            assert resp.status_code == 200
            assert resp.json() == []

    def test_returns_campaigns(self):
        mock_sb = _mock_supabase()
        mock_sb.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(data=[
            {"id": "1", "offer_id": "o1", "slug": "test-campaign", "title": "Test Campaign", "status": "draft"},
        ])

        with patch("app.routes.campaigns.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.get("/api/campaigns")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["slug"] == "test-campaign"


class TestGetCampaign:
    def test_returns_404_when_not_found(self):
        mock_sb = _mock_supabase()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        with patch("app.routes.campaigns.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.get("/api/campaigns/nonexistent")
            assert resp.status_code == 404

    def test_returns_campaign_when_found(self):
        mock_sb = _mock_supabase()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[
            {"id": "1", "offer_id": "o1", "slug": "found", "title": "Found Campaign", "status": "active"},
        ])

        with patch("app.routes.campaigns.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.get("/api/campaigns/found")
            assert resp.status_code == 200
            data = resp.json()
            assert data["slug"] == "found"


class TestCreateCampaign:
    def test_returns_201(self):
        mock_sb = _mock_supabase()
        # First call: offer lookup
        offer_result = MagicMock(data=[{"id": "offer-123"}])
        # Second call: campaign insert
        campaign_result = MagicMock(data=[
            {"id": "new-id", "offer_id": "offer-123", "slug": "test-campaign", "title": "Test Campaign",
             "status": "draft", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"},
        ])

        # Chain: table("offers").select("id").eq("slug", ...).execute() -> offer_result
        # Chain: table("campaigns").insert({...}).execute() -> campaign_result
        offers_table = MagicMock()
        offers_table.select.return_value.eq.return_value.execute.return_value = offer_result
        campaigns_table = MagicMock()
        campaigns_table.insert.return_value.execute.return_value = campaign_result

        def table_router(name):
            if name == "offers":
                return offers_table
            return campaigns_table

        mock_sb.table.side_effect = table_router

        with patch("app.routes.campaigns.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.post("/api/campaigns", json={
                "offer_slug": "test-offer",
                "name": "Test Campaign",
            })
            assert resp.status_code == 201
            data = resp.json()
            assert data["slug"] == "test-campaign"
            assert data["title"] == "Test Campaign"
            assert data["status"] == "draft"

    def test_returns_404_when_offer_not_found(self):
        mock_sb = _mock_supabase()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        with patch("app.routes.campaigns.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.post("/api/campaigns", json={
                "offer_slug": "nonexistent-offer",
                "name": "Test Campaign",
            })
            assert resp.status_code == 404
