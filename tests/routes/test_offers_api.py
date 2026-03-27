"""Offers API route tests."""

from fastapi.testclient import TestClient

from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_list_offers_returns_empty():
    client = _client()
    resp = client.get("/api/offers")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_offer_returns_404():
    client = _client()
    resp = client.get("/api/offers/nonexistent")
    assert resp.status_code == 404


def test_create_offer_returns_201():
    client = _client()
    resp = client.post("/api/offers", json={
        "name": "Test Offer",
        "description": "A test offer",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["slug"] == "test-offer"
    assert data.get("name") == "Test Offer" or data.get("title") == "Test Offer" or data.get("slug") == "test-offer"
    assert data["status"] == "draft"
