"""Offers API route tests."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def _mock_supabase():
    """Create a mock supabase client with chainable table methods."""
    mock = MagicMock()
    return mock


class TestListOffers:
    def test_returns_empty_list(self):
        mock_sb = _mock_supabase()
        mock_sb.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(data=[])

        with patch("app.routes.offers.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.get("/api/offers")
            assert resp.status_code == 200
            assert resp.json() == []

    def test_returns_offers(self):
        mock_sb = _mock_supabase()
        mock_sb.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(data=[
            {"id": "1", "slug": "test-offer", "title": "Test Offer", "description": "", "status": "draft"},
        ])

        with patch("app.routes.offers.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.get("/api/offers")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["slug"] == "test-offer"


class TestGetOffer:
    def test_returns_404_when_not_found(self):
        mock_sb = _mock_supabase()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        with patch("app.routes.offers.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.get("/api/offers/nonexistent")
            assert resp.status_code == 404

    def test_returns_offer_when_found(self):
        mock_sb = _mock_supabase()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[
            {"id": "1", "slug": "found", "title": "Found Offer", "description": "desc", "status": "active"},
        ])

        with patch("app.routes.offers.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.get("/api/offers/found")
            assert resp.status_code == 200
            data = resp.json()
            assert data["slug"] == "found"


class TestCreateOffer:
    def test_returns_201(self):
        mock_sb = _mock_supabase()
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[
            {"id": "new-id", "slug": "test-offer", "title": "Test Offer", "description": "A test offer", "status": "draft",
             "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"},
        ])

        with patch("app.routes.offers.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.post("/api/offers", json={
                "name": "Test Offer",
                "description": "A test offer",
            })
            assert resp.status_code == 201
            data = resp.json()
            assert data["slug"] == "test-offer"
            assert data["status"] == "draft"

    def test_conflict_returns_409(self):
        mock_sb = _mock_supabase()
        mock_sb.table.return_value.insert.return_value.execute.side_effect = Exception("duplicate key value violates unique constraint 23505")

        with patch("app.routes.offers.get_supabase_client", return_value=mock_sb):
            client = _client()
            resp = client.post("/api/offers", json={
                "name": "Test Offer",
                "description": "A test offer",
            })
            assert resp.status_code == 409
