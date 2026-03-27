"""Skills API routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog
from fastapi import APIRouter, Query, Request

from app.config import get_settings
from app.errors import AppError
from app.sse import sse_skill_stream
from models.api import RunSkillRequest, RunSkillResponse, SkillStatusResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/skills", tags=["skills"])

# Expected output files per skill
SKILL_OUTPUTS: dict[int, list[str]] = {
    1: ["positioning.md"],
    2: ["strategy.md"],
    3: ["copy/email-variants.md", "copy/linkedin-variants.md", "copy/personalization-notes.md"],
    4: ["leads/all_leads.csv"],
    5: ["outreach/messages.csv"],
    6: ["results/learnings.md"],
}


@router.post("/run", response_model=RunSkillResponse)
async def run_skill(req: RunSkillRequest) -> RunSkillResponse:
    """Queue a skill run via Celery and return the task ID."""
    try:
        from workers.skill_tasks import run_skill_task

        result = run_skill_task.delay(
            skill_id=req.skill_id,
            offer_slug=req.offer_slug,
            campaign_slug=req.campaign_slug,
            config=req.config,
        )
        return RunSkillResponse(
            task_id=result.id,
            status="queued",
            message=f"Skill {req.skill_id} queued for {req.offer_slug}",
        )
    except Exception as exc:
        logger.warning("Celery dispatch failed, returning error: %s", exc)
        raise AppError(
            message=f"Failed to queue skill: {exc}",
            status_code=503,
            code="QUEUE_UNAVAILABLE",
        )


@router.get("/status", response_model=SkillStatusResponse)
async def skill_status(
    offer_slug: str = Query(...),
    campaign_slug: str = Query(None),
    skill_id: int = Query(...),
) -> SkillStatusResponse:
    """Check filesystem for skill outputs."""
    settings = get_settings()
    offers_root = Path(settings.offers_dir).resolve()
    base = (offers_root / offer_slug).resolve()
    if campaign_slug:
        base = (base / "campaigns" / campaign_slug).resolve()

    # Path traversal protection
    if not base.is_relative_to(offers_root):
        return SkillStatusResponse(
            skill_id=skill_id,
            offer_slug=offer_slug,
            campaign_slug=campaign_slug,
            outputs={fname: False for fname in SKILL_OUTPUTS.get(skill_id, [])},
        )

    expected = SKILL_OUTPUTS.get(skill_id, [])
    outputs: dict[str, bool] = {}
    for fname in expected:
        outputs[fname] = (base / fname).exists()

    return SkillStatusResponse(
        skill_id=skill_id,
        offer_slug=offer_slug,
        campaign_slug=campaign_slug,
        outputs=outputs,
    )


@router.get("/run-summary")
async def run_summary(
    offer: str = Query(...),
    campaign: str = Query(...),
) -> dict[str, Any]:
    """Read run-summary.json from the campaign leads directory."""
    settings = get_settings()
    offers_root = Path(settings.offers_dir).resolve()
    path = (
        offers_root
        / offer
        / "campaigns"
        / campaign
        / "leads"
        / "run-summary.json"
    ).resolve()

    # Path traversal protection
    if not path.is_relative_to(offers_root):
        raise AppError(message="run-summary.json not found", status_code=404, code="NOT_FOUND")

    if not path.exists():
        raise AppError(message="run-summary.json not found", status_code=404, code="NOT_FOUND")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/stream")
async def skill_stream(
    request: Request,
    offer: str = Query(...),
    campaign: str = Query(...),
    skill: int = Query(...),
):
    """SSE stream for skill execution logs via Redis pub/sub."""
    settings = get_settings()
    channel = f"skill-run:{offer}:{campaign}:{skill}"
    return await sse_skill_stream(channel, settings.redis_url, request)
