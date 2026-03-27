"""Celery Beat scheduled tasks (stubs)."""

from __future__ import annotations

import logging

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="run_agent_cron")
def run_agent_cron():
    """Daily agent run triggered by Celery Beat at 09:00 UTC.

    Stub — will trigger the full agent pipeline for all active campaigns.
    """
    logger.info("Agent cron triggered")
    return {"status": "completed", "task": "agent_cron"}


@celery_app.task(name="run_health_monitor")
def run_health_monitor():
    """Health monitor triggered every 6 hours by Celery Beat.

    Stub — will check API connectivity, quota usage, stale campaigns, etc.
    """
    logger.info("Health monitor triggered")
    return {"status": "healthy", "task": "health_monitor"}


@celery_app.task(name="cleanup_stale_runs")
def cleanup_stale_runs():
    """Cleanup stale skill runs triggered daily at 03:00 UTC by Celery Beat.

    Stub — will mark hung runs as failed and clean up temporary resources.
    """
    logger.info("Cleanup stale runs triggered")
    return {"status": "completed", "task": "cleanup_stale_runs"}
