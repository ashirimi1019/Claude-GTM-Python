"""Campaigns CRUD API routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter

from app.errors import AppError, to_app_error, error_response
from clients.supabase_client import get_supabase_client
from models.campaign import Campaign, CampaignCreate

logger = structlog.get_logger()
router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=list[Campaign])
async def list_campaigns() -> list[Campaign]:
    """Return all campaigns ordered by created_at desc."""
    try:
        sb = get_supabase_client()
        result = sb.table("campaigns").select("*").order("created_at", desc=True).execute()
        return [Campaign.model_validate(row) for row in result.data]
    except Exception as exc:
        logger.error("list_campaigns failed", fn="list_campaigns", err=str(exc))
        raise to_app_error(exc)


@router.get("/{slug}", response_model=Campaign)
async def get_campaign(slug: str) -> Campaign:
    """Return a single campaign by slug."""
    try:
        sb = get_supabase_client()
        result = sb.table("campaigns").select("*").eq("slug", slug).execute()
        if not result.data:
            raise AppError(
                message=f"Campaign '{slug}' not found",
                status_code=404,
                code="NOT_FOUND",
            )
        return Campaign.model_validate(result.data[0])
    except AppError:
        raise
    except Exception as exc:
        logger.error("get_campaign failed", fn="get_campaign", slug=slug, err=str(exc))
        raise to_app_error(exc)


@router.post("", response_model=Campaign, status_code=201)
async def create_campaign(body: CampaignCreate) -> Campaign:
    """Create a new campaign. Looks up offer_id from offer_slug."""
    try:
        sb = get_supabase_client()

        # Look up offer by slug to get offer_id
        offer_result = sb.table("offers").select("id").eq("slug", body.offer_slug).execute()
        if not offer_result.data:
            raise AppError(
                message=f"Offer '{body.offer_slug}' not found",
                status_code=404,
                code="NOT_FOUND",
            )
        offer_id = offer_result.data[0]["id"]

        row = {
            "id": str(uuid.uuid4()),
            "offer_id": offer_id,
            "slug": body.slug,
            "title": body.name,
            "vertical_id": body.vertical_id or None,
            "status": "draft",
            "allowed_countries": body.allowed_countries,
            "allowed_us_states": body.allowed_us_states,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        result = sb.table("campaigns").insert(row).execute()
        return Campaign.model_validate(result.data[0])
    except AppError:
        raise
    except Exception as exc:
        err_str = str(exc)
        if "duplicate" in err_str.lower() or "23505" in err_str:
            raise AppError(
                message=f"Campaign with slug '{body.slug}' already exists",
                status_code=409,
                code="CONFLICT",
            )
        logger.error("create_campaign failed", fn="create_campaign", err=err_str)
        raise to_app_error(exc)
