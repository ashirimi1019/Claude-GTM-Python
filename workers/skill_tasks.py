"""Celery tasks for skills 1-6 — wired to real skill implementations."""

from __future__ import annotations

from typing import Any

import structlog
from asgiref.sync import async_to_sync

from core.skills.skill_1_new_offer import run_skill_1
from core.skills.skill_2_campaign_strategy import run_skill_2
from core.skills.skill_3_campaign_copy import run_skill_3
from core.skills.skill_4_find_leads import run_skill_4
from core.skills.skill_5_launch_outreach import run_skill_5
from core.skills.skill_6_campaign_review import run_skill_6
from services.run_tracker import SkillRunTracker
from workers.celery_app import celery_app

logger = structlog.get_logger()

# Registry mapping skill_id → async skill function (populated eagerly at module level)
_SKILL_REGISTRY: dict[int, Any] = {
    1: run_skill_1,
    2: run_skill_2,
    3: run_skill_3,
    4: run_skill_4,
    5: run_skill_5,
    6: run_skill_6,
}


def _get_skill_fn(skill_id: int):
    """Look up a skill function by ID."""
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
        "Running skill",
        skill_id=skill_id,
        offer_slug=offer_slug,
        campaign_slug=campaign_slug,
        task_id=self.request.id,
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

        # Send SSE termination event so frontend knows the stream is complete
        try:
            broker_url = celery_app.conf.get("broker_url", "")
            if broker_url:
                tracker = SkillRunTracker(
                    skill_id=skill_id,
                    offer_slug=offer_slug,
                    campaign_slug=campaign_slug,
                    redis_url=broker_url,
                )
                tracker.finish()
        except Exception:
            pass  # Best-effort SSE termination

        return {
            "status": "completed",
            "skill_id": skill_id,
            "offer_slug": offer_slug,
            "campaign_slug": campaign_slug,
            "task_id": self.request.id,
            "result": result,
        }

    except Exception as e:
        logger.error("Skill failed", skill_id=skill_id, error=str(e), exc_info=True)
        # Publish error to Redis so SSE clients are notified
        try:
            from workers.celery_app import celery_app as _app
            redis_url = _app.conf.get("broker_url", "")
            if redis_url:
                import redis as _redis
                _r = _redis.from_url(redis_url)
                import json as _json
                _r.publish(
                    f"skill-run:{offer_slug}:{campaign_slug or 'none'}:{skill_id}",
                    _json.dumps({"type": "error", "error": str(e)}),
                )
        except Exception:
            pass  # Best-effort SSE notification
        # Re-raise so Celery marks the task as FAILURE and can retry
        raise
