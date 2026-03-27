"""Agents API routes."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from app.config import get_settings
from app.errors import AppError
from models.api import AgentConfigRequest, ApproveActionRequest, RunAgentsRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


async def verify_agent_secret(
    x_agent_secret: str = Header(...),
) -> str:
    """Dependency that validates the x-agent-secret header."""
    settings = get_settings()
    if not settings.agent_internal_secret:
        raise HTTPException(status_code=500, detail="agent_internal_secret not configured")
    if x_agent_secret != settings.agent_internal_secret:
        raise HTTPException(status_code=403, detail="Invalid agent secret")
    return x_agent_secret


@router.post("/run")
async def run_agents(req: RunAgentsRequest) -> dict[str, str]:
    """Launch agent pipeline via Celery."""
    try:
        from workers.agent_tasks import run_agent_pipeline

        result = run_agent_pipeline.delay(
            offer_slug=req.offer_slug,
            campaign_slug=req.campaign_slug,
        )
        return {
            "task_id": result.id,
            "status": "queued",
            "message": f"Agents queued for {req.offer_slug}/{req.campaign_slug}",
        }
    except Exception as exc:
        logger.warning("Celery dispatch failed for agents: %s", exc)
        raise AppError(
            message=f"Failed to queue agent pipeline: {exc}",
            status_code=503,
            code="QUEUE_UNAVAILABLE",
        )


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
