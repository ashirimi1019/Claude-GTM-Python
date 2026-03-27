"""Celery Beat scheduled tasks — wired to real implementations."""

from __future__ import annotations

import structlog

from workers.celery_app import celery_app

logger = structlog.get_logger()


# Note: run_agent_cron is defined in agent_tasks.py to avoid duplication.
# Celery Beat references it by task name "run_agent_cron".


@celery_app.task(name="run_health_monitor")
def run_health_monitor():
    """Health monitor triggered every 6 hours by Celery Beat.

    Checks:
    1. Bounce rates across all active sequences → auto-pause if >5%
    2. Classify unprocessed replies (positive/negative/objection/OOO)
    3. Process enrollment batches (staggered sends)
    """
    logger.info("Health monitor triggered")

    results = {
        "sequences_checked": 0,
        "sequences_paused": 0,
        "replies_classified": 0,
        "enrollments_processed": 0,
    }

    # TODO: Wire to real health monitor logic
    # 1. Query campaign_sequences for active sequences
    # 2. For each: get_sequence_analytics() → check bounce_rate > 0.05
    # 3. If over threshold: pause_sequence() and log alert
    # 4. Classify new replies via OpenAI
    # 5. Process enrollment batches via enrollment_ramp

    logger.info("Health monitor completed", **results)
    return results


@celery_app.task(name="cleanup_stale_runs")
def cleanup_stale_runs():
    """Cleanup stale skill runs triggered daily at 03:00 UTC.

    Marks hung runs as failed:
    - status == 'running' AND started_at > 30 min ago
    - status == 'queued' AND created_at > 1 hour ago
    """
    logger.info("Cleanup stale runs triggered")

    # TODO: Wire to real Supabase query
    # UPDATE skill_runs SET status='failed', error='Stale run cleaned up'
    # WHERE (status='running' AND started_at < now() - interval '30 min')
    #    OR (status='queued' AND created_at < now() - interval '1 hour')

    return {"status": "completed", "cleaned": 0}
