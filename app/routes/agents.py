"""Agents API routes."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Query

from models.api import AgentConfigRequest, ApproveActionRequest, RunAgentsRequest

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/run")
async def run_agents(req: RunAgentsRequest) -> dict[str, str]:
    """Launch agent run for a campaign (stub)."""
    return {
        "task_id": str(uuid.uuid4()),
        "status": "queued",
        "message": f"Agents queued for {req.offer_slug}/{req.campaign_slug}",
    }


@router.get("/config")
async def get_agent_config(campaign_id: str = Query(...)) -> dict[str, Any]:
    """Return autonomy config for a campaign (stub)."""
    return {
        "campaign_id": campaign_id,
        "autonomy_level": "supervised",
        "auto_apply": False,
        "agents_enabled": False,
    }


@router.post("/config")
async def save_agent_config(req: AgentConfigRequest) -> dict[str, Any]:
    """Save agent config (stub)."""
    return {
        "campaign_id": req.campaign_id,
        "autonomy_level": req.autonomy_level,
        "auto_apply": req.auto_apply,
        "saved": True,
    }


@router.get("/approve")
async def list_pending_approvals() -> list[dict[str, Any]]:
    """Return pending approval actions (stub)."""
    return []


@router.post("/approve")
async def approve_action(req: ApproveActionRequest) -> dict[str, Any]:
    """Approve or reject an agent action (stub)."""
    return {
        "action_id": req.action_id,
        "approved": req.approved,
        "processed": True,
    }
