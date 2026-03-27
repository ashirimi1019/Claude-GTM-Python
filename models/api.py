"""API request/response schemas for FastAPI routes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# --- Skills API ---

class RunSkillRequest(BaseModel):
    """POST /api/skills/run"""
    skill_id: int
    offer_slug: str
    campaign_slug: str | None = None
    config: dict[str, Any] | None = None


class RunSkillResponse(BaseModel):
    """Response from POST /api/skills/run"""
    task_id: str
    status: str = "queued"
    message: str = ""


class SkillStatusResponse(BaseModel):
    """GET /api/skills/status"""
    skill_id: int
    offer_slug: str
    campaign_slug: str | None = None
    outputs: dict[str, bool] = {}  # filename → exists


# --- ICP API ---

class IcpPreviewRequest(BaseModel):
    """POST /api/icp/preview"""
    campaign_id: str | None = None
    offer_id: str | None = None
    icp_profile: dict[str, Any] | None = None
    source: str = "db"  # db | live | inline
    companies: list[dict[str, Any]] | None = None


class IcpPreviewResponse(BaseModel):
    """Response from POST /api/icp/preview"""
    model_config = {"populate_by_name": True}
    summary: dict[str, Any] = {}
    rejection_breakdown: dict[str, int] = {}
    top_rejection_reasons: list[dict[str, Any]] = []
    tier_distribution: dict[str, int] = {}
    confidence_stats: dict[str, float] = {}
    score_stats: dict[str, float] | None = None
    effective_config: dict[str, Any] = {}
    sample_traces: list[dict[str, Any]] = []
    two_stage_info: dict[str, Any] | None = None
    meta: dict[str, Any] = Field(default_factory=dict, alias="_meta")


# --- Agents API ---

class RunAgentsRequest(BaseModel):
    """POST /api/agents/run"""
    offer_slug: str
    campaign_slug: str


class AgentConfigRequest(BaseModel):
    """POST /api/agents/config"""
    campaign_id: str
    autonomy_level: str = "supervised"  # supervised | semi-autonomous | autonomous
    auto_apply: bool = False


class ApproveActionRequest(BaseModel):
    """POST /api/agents/approve"""
    action_id: str
    approved: bool
    reason: str = ""
