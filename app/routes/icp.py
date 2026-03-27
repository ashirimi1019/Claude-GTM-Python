"""ICP (Ideal Customer Profile) API routes."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter

from app.errors import AppError, to_app_error
from clients.supabase_client import get_supabase_client
from models.api import IcpPreviewRequest, IcpPreviewResponse
from services.icp.preview import run_icp_preview
from services.icp.validator import validate_icp_profile

logger = structlog.get_logger()
router = APIRouter(tags=["icp"])


@router.get("/campaigns/{campaign_id}/icp-profile")
async def get_icp_profile(campaign_id: str) -> dict[str, Any]:
    """Return the ICP profile for a campaign."""
    try:
        sb = get_supabase_client()
        result = sb.table("campaigns").select("id, icp_profile").eq("id", campaign_id).execute()
        if not result.data:
            raise AppError(
                message=f"Campaign '{campaign_id}' not found",
                status_code=404,
                code="NOT_FOUND",
            )
        row = result.data[0]
        icp_profile = row.get("icp_profile")
        if icp_profile is None:
            raise AppError(
                message=f"ICP profile for campaign '{campaign_id}' not found",
                status_code=404,
                code="NOT_FOUND",
            )
        return {"campaign_id": campaign_id, "icp_profile": icp_profile}
    except AppError:
        raise
    except Exception as exc:
        logger.error("get_icp_profile failed", fn="get_icp_profile", campaign_id=campaign_id, err=str(exc))
        raise to_app_error(exc)


@router.post("/campaigns/{campaign_id}/icp-profile")
async def save_icp_profile(campaign_id: str, body: dict[str, Any]) -> dict[str, Any]:
    """Save ICP profile for a campaign. Validates with validate_icp_profile first."""
    try:
        # Validate the profile
        validation = validate_icp_profile(body)
        if not validation["valid"]:
            raise AppError(
                message=f"Invalid ICP profile: {'; '.join(validation['errors'])}",
                status_code=422,
                code="VALIDATION_ERROR",
            )

        sb = get_supabase_client()

        # Check campaign exists
        check = sb.table("campaigns").select("id").eq("id", campaign_id).execute()
        if not check.data:
            raise AppError(
                message=f"Campaign '{campaign_id}' not found",
                status_code=404,
                code="NOT_FOUND",
            )

        # Update icp_profile
        sb.table("campaigns").update({"icp_profile": body}).eq("id", campaign_id).execute()
        return {"campaign_id": campaign_id, "icp_profile": body, "saved": True}
    except AppError:
        raise
    except Exception as exc:
        logger.error("save_icp_profile failed", fn="save_icp_profile", campaign_id=campaign_id, err=str(exc))
        raise to_app_error(exc)


@router.post("/icp/preview", response_model=IcpPreviewResponse)
async def icp_preview(req: IcpPreviewRequest) -> IcpPreviewResponse:
    """Preview ICP scoring results."""
    try:
        if req.companies and len(req.companies) > 500:
            raise AppError(
                message=f"Too many companies: {len(req.companies)} (max 500)",
                status_code=422,
                code="VALIDATION_ERROR",
            )
        if req.icp_profile and req.companies:
            # Actually run the preview pipeline
            result = run_icp_preview(
                profile=req.icp_profile,
                companies=req.companies,
            )
            return IcpPreviewResponse(
                summary=result.get("summary", {}),
                rejection_breakdown=result.get("rejectionBreakdown", {}),
                top_rejection_reasons=result.get("topRejectionReasons", []),
                tier_distribution=result.get("tierDistribution", {}),
                confidence_stats=result.get("confidenceStats", {}),
                score_stats=result.get("scoreStats"),
                effective_config=result.get("effectiveConfig", {}),
                sample_traces=result.get("sampleTraces", []),
                two_stage_info=result.get("twoStageInfo"),
            )
        elif req.icp_profile:
            # Profile provided but no companies — return effective config
            return IcpPreviewResponse(
                summary={"total_companies": 0, "qualified": 0},
                tier_distribution={"tier_1": 0, "tier_2": 0, "tier_3": 0},
                effective_config=req.icp_profile,
            )
        return IcpPreviewResponse(
            summary={"total_companies": 0, "qualified": 0},
            effective_config={},
        )
    except AppError:
        raise
    except Exception as exc:
        logger.error("icp_preview failed", fn="icp_preview", err=str(exc))
        raise to_app_error(exc)
