"""Cron routes — stale run cleanup and maintenance."""

from __future__ import annotations

from fastapi import APIRouter

import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/cron", tags=["cron"])


@router.post("/cleanup-stale-runs")
async def cleanup_stale_runs():
    """Clean up stale skill runs that have been running for too long.

    A run is considered stale if:
    - status == 'running' AND started_at > 30 minutes ago
    - status == 'queued' AND created_at > 1 hour ago

    This endpoint is called daily at 3am UTC via Celery Beat.
    """
    cleaned = 0

    # TODO: Query skill_runs table for stale entries
    # Update status to 'failed' with error message 'Stale run cleaned up'

    logger.info("Stale run cleanup completed", cleaned=cleaned)
    return {"cleaned": cleaned}
