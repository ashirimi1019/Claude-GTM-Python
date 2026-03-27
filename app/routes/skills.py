"""Skills API routes."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.errors import AppError
from models.api import RunSkillRequest, RunSkillResponse, SkillStatusResponse

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
    """Queue a skill run and return a task ID."""
    task_id = str(uuid.uuid4())
    return RunSkillResponse(
        task_id=task_id,
        status="queued",
        message=f"Skill {req.skill_id} queued for {req.offer_slug}",
    )


@router.get("/status", response_model=SkillStatusResponse)
async def skill_status(
    offer_slug: str = Query(...),
    campaign_slug: str = Query(None),
    skill_id: int = Query(...),
) -> SkillStatusResponse:
    """Check filesystem for skill outputs."""
    settings = get_settings()
    base = Path(settings.offers_dir) / offer_slug
    if campaign_slug:
        base = base / "campaigns" / campaign_slug

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
    path = (
        Path(settings.offers_dir)
        / offer
        / "campaigns"
        / campaign
        / "leads"
        / "run-summary.json"
    )
    if not path.exists():
        raise AppError(message="run-summary.json not found", status_code=404, code="NOT_FOUND")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/stream")
async def skill_stream(
    offer: str = Query(...),
    campaign: str = Query(...),
    skill: int = Query(...),
) -> StreamingResponse:
    """SSE placeholder for streaming skill execution logs."""

    async def event_generator():
        yield f"data: {{\"skill\": {skill}, \"status\": \"connected\"}}\n\n"
        yield "data: {\"status\": \"done\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
