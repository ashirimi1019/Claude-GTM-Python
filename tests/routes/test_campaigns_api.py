"""Campaigns API route tests."""

from fastapi.testclient import TestClient

from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_list_campaigns_returns_empty():
    client = _client()
    resp = client.get("/api/campaigns")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_campaign_returns_404():
    client = _client()
    resp = client.get("/api/campaigns/nonexistent")
    assert resp.status_code == 404


def test_create_campaign_returns_201():
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
