"""SkillRunTracker — publishes SSE events via Redis pub/sub."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import redis

logger = logging.getLogger(__name__)


class SkillRunTracker:
    """Tracks skill run progress and publishes events over Redis pub/sub.

    Each skill run gets a unique channel:
        skill-run:{offer_slug}:{campaign_slug}:{skill_id}

    Frontend clients subscribe via SSE to receive real-time updates.
    """

    def __init__(
        self,
        skill_id: int,
        offer_slug: str,
        campaign_slug: str | None,
        redis_url: str,
    ):
        self.skill_id = skill_id
        self.offer_slug = offer_slug
        self.campaign_slug = campaign_slug
        self.redis_client = redis.from_url(redis_url)
        self.channel = f"skill-run:{offer_slug}:{campaign_slug or 'none'}:{skill_id}"
        self.steps: list[dict] = []

    def _publish(self, entry: dict) -> None:
        """Publish an entry to the Redis channel and append to local log."""
        self.steps.append(entry)
        try:
            self.redis_client.publish(self.channel, json.dumps(entry))
        except redis.RedisError:
            logger.warning("Failed to publish to Redis channel %s", self.channel)

    def log(self, message: str, level: str = "info") -> None:
        """Log a freeform message."""
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
        }
        self._publish(entry)

    def start_step(self, name: str) -> None:
        """Mark a named step as started."""
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": "info",
            "message": f"Step started: {name}",
            "step": name,
            "step_status": "started",
        }
        self._publish(entry)

    def complete_step(self, name: str) -> None:
        """Mark a named step as completed."""
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": "info",
            "message": f"Step completed: {name}",
            "step": name,
            "step_status": "completed",
        }
        self._publish(entry)

    def fail_step(self, name: str, error: str) -> None:
        """Mark a named step as failed."""
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": "error",
            "message": f"Step failed: {name} — {error}",
            "step": name,
            "step_status": "failed",
            "error": error,
        }
        self._publish(entry)
