"""Celery tasks for skills 1-6 — wired to real skill implementations."""

from __future__ import annotations

import logging
from typing import Any

from asgiref.sync import async_to_sync

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Registry mapping skill_id → async skill function
_SKILL_REGISTRY: dict[int, Any] = {}


def _get_skill_fn(skill_id: int):
    """Lazy-load skill functions to avoid circular imports."""
    if not _SKILL_REGISTRY:
        from core.skills.skill_1_new_offer import run_skill_1
        from core.skills.skill_2_campaign_strategy import run_skill_2
        from core.skills.skill_3_campaign_copy import run_skill_3
        from core.skills.skill_4_find_leads import run_skill_4
        from core.skills.skill_5_launch_outreach import run_skill_5
        from core.skills.skill_6_campaign_review import run_skill_6

        _SKILL_REGISTRY.update({
            1: run_skill_1,
            2: run_skill_2,
            3: run_skill_3,
            4: run_skill_4,
            5: run_skill_5,
            6: run_skill_6,
        })

    fn = _SKILL_REGISTRY.get(skill_id)
    if fn is None:
        raise ValueError(f"Unknown skill_id: {skill_id}")
    return fn


@celery_app.task(bind=True, name="run_skill")
def run_skill_task(
    self,
    skill_id: int,
    offer_slug: str,
    campaign_slug: str | None = None,
    config: dict | None = None,
):
    """Execute a skill as a background Celery task.

    Skills 1-2 take a config dict. Skills 3-6 take offer_slug + campaign_slug.
    """
    logger.info(
        "Running skill %d for offer=%s campaign=%s task_id=%s",
        skill_id,
        offer_slug,
        campaign_slug,
        self.request.id,
    )

    try:
        skill_fn = _get_skill_fn(skill_id)

        if skill_id == 1:
            # Skill 1: config-driven
            result = async_to_sync(skill_fn)(config or {"name": offer_slug})
        elif skill_id == 2:
            # Skill 2: config-driven
            cfg = config or {"offer_slug": offer_slug, "name": campaign_slug or "default"}
            result = async_to_sync(skill_fn)(cfg)
        else:
            # Skills 3-6: offer_slug + campaign_slug
            result = async_to_sync(skill_fn)(offer_slug, campaign_slug or "")

        return {
            "status": "completed",
            "skill_id": skill_id,
            "offer_slug": offer_slug,
            "campaign_slug": campaign_slug,
            "task_id": self.request.id,
            "result": result,
        }

    except Exception as e:
        logger.error("Skill %d failed: %s", skill_id, str(e), exc_info=True)
        return {
            "status": "failed",
            "skill_id": skill_id,
            "offer_slug": offer_slug,
            "campaign_slug": campaign_slug,
            "task_id": self.request.id,
            "error": str(e),
        }
