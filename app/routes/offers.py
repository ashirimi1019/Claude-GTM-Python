"""Offers CRUD API routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from app.errors import AppError
from models.offer import Offer, OfferCreate

router = APIRouter(prefix="/offers", tags=["offers"])


@router.get("", response_model=list[Offer])
async def list_offers() -> list[Offer]:
    """Return all offers (stub: empty list)."""
    return []


@router.get("/{slug}", response_model=Offer)
async def get_offer(slug: str) -> Offer:
    """Return a single offer by slug (stub)."""
    # Real implementation would query Supabase
    raise AppError(
        message=f"Offer '{slug}' not found",
        status_code=404,
        code="NOT_FOUND",
    )


@router.post("", response_model=Offer, status_code=201)
async def create_offer(body: OfferCreate) -> Offer:
    """Create a new offer (stub: returns mock)."""
    return Offer(
        id=str(uuid.uuid4()),
        slug=body.slug,
        name=body.name,
        description=body.description,
        default_vertical_id=body.vertical_id,
        status="draft",
        allowed_countries=body.allowed_countries,
        allowed_us_states=body.allowed_us_states,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
