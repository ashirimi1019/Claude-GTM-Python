"""Offers CRUD API routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter

from app.errors import AppError, to_app_error, error_response
from clients.supabase_client import get_supabase_client
from models.offer import Offer, OfferCreate

logger = structlog.get_logger()
router = APIRouter(prefix="/offers", tags=["offers"])


@router.get("", response_model=list[Offer])
async def list_offers() -> list[Offer]:
    """Return all offers ordered by created_at desc."""
    try:
        sb = get_supabase_client()
        result = sb.table("offers").select("*").order("created_at", desc=True).execute()
        return [Offer.model_validate(row) for row in result.data]
    except Exception as exc:
        logger.error("list_offers failed", fn="list_offers", err=str(exc))
        raise to_app_error(exc)


@router.get("/{slug}", response_model=Offer)
async def get_offer(slug: str) -> Offer:
    """Return a single offer by slug."""
    try:
        sb = get_supabase_client()
        result = sb.table("offers").select("*").eq("slug", slug).execute()
        if not result.data:
            raise AppError(
                message=f"Offer '{slug}' not found",
                status_code=404,
                code="NOT_FOUND",
            )
        return Offer.model_validate(result.data[0])
    except AppError:
        raise
    except Exception as exc:
        logger.error("get_offer failed", fn="get_offer", slug=slug, err=str(exc))
        raise to_app_error(exc)


@router.post("", response_model=Offer, status_code=201)
async def create_offer(body: OfferCreate) -> Offer:
    """Create a new offer."""
    try:
        sb = get_supabase_client()
        row = {
            "id": str(uuid.uuid4()),
            "slug": body.slug,
            "title": body.name,
            "description": body.description,
            "default_vertical_id": body.vertical_id or None,
            "status": "draft",
            "allowed_countries": body.allowed_countries,
            "allowed_us_states": body.allowed_us_states,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        result = sb.table("offers").insert(row).execute()
        return Offer.model_validate(result.data[0])
    except Exception as exc:
        err_str = str(exc)
        # Handle unique constraint violation gracefully
        if "duplicate" in err_str.lower() or "23505" in err_str:
            raise AppError(
                message=f"Offer with slug '{body.slug}' already exists",
                status_code=409,
                code="CONFLICT",
            )
        logger.error("create_offer failed", fn="create_offer", err=err_str)
        raise to_app_error(exc)
