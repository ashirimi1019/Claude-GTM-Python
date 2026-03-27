"""ICP (Ideal Customer Profile) API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.errors import AppError
from models.api import IcpPreviewRequest, IcpPreviewResponse

router = APIRouter(tags=["icp"])


@router.get("/campaigns/{campaign_id}/icp-profile")
async def get_icp_profile(campaign_id: str) -> dict[str, Any]:
    """Return the ICP profile for a campaign (stub)."""
    raise AppError(
        message=f"ICP profile for campaign '{campaign_id}' not found",
        status_code=404,
        code="NOT_FOUND",
    )


@router.post("/campaigns/{campaign_id}/icp-profile")
async def save_icp_profile(campaign_id: str, body: dict[str, Any]) -> dict[str, Any]:
    """Save ICP profile for a campaign (stub)."""
    return {"campaign_id": campaign_id, "icp_profile": body, "saved": True}


@router.post("/icp/preview", response_model=IcpPreviewResponse)
async def icp_preview(req: IcpPreviewRequest) -> IcpPreviewResponse:
    """Preview ICP scoring results."""
    if req.icp_profile:
        # Stub: return a mock preview based on the provided profile
        return IcpPreviewResponse(
            summary={"total_companies": 0, "qualified": 0},
            tier_distribution={"tier_1": 0, "tier_2": 0, "tier_3": 0},
            effective_config=req.icp_profile,
        )
    return IcpPreviewResponse(
        summary={"total_companies": 0, "qualified": 0},
        effective_config={},
    )
