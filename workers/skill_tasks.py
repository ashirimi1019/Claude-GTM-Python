"""Celery tasks for skills 1-6."""

from __future__ import annotations

import logging

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="run_skill")
def run_skill_task(
    self,
    skill_id: int,
    offer_slug: str,
    campaign_slug: str | None = None,
    config: dict | None = None,
):
    """Execute a skill as a background Celery task.

    Real skill implementations will be wired in later.
    """
    logger.info(
        "Running skill %d for offer=%s campaign=%s task_id=%s",
        skill_id,
        offer_slug,
        campaign_slug,
        self.request.id,
    )
    return {
        "status": "completed",
        "skill_id": skill_id,
        "offer_slug": offer_slug,
        "campaign_slug": campaign_slug,
        "task_id": self.request.id,
    }
