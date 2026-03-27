"""Campaigns CRUD API routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from app.errors import AppError
from models.campaign import Campaign, CampaignCreate

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=list[Campaign])
async def list_campaigns() -> list[Campaign]:
    """Return all campaigns (stub: empty list)."""
    return []


@router.get("/{slug}", response_model=Campaign)
async def get_campaign(slug: str) -> Campaign:
    """Return a single campaign by slug (stub)."""
    raise AppError(
        message=f"Campaign '{slug}' not found",
        status_code=404,
        code="NOT_FOUND",
    )


@router.post("", response_model=Campaign, status_code=201)
async def create_campaign(body: CampaignCreate) -> Campaign:
    """Create a new campaign (stub: returns mock)."""
    return Campaign(
        id=str(uuid.uuid4()),
        offer_id="stub-offer-id",
        slug=body.slug,
        title=body.name,
        vertical_id=body.vertical_id,
        status="draft",
        allowed_countries=body.allowed_countries,
        allowed_us_states=body.allowed_us_states,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
