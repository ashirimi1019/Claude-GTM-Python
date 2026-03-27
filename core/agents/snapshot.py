"""Campaign state snapshot builder for agent reasoning."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()


async def build_snapshot(campaign_slug: str) -> dict[str, Any]:
    """Build campaign state snapshot from DB for agent reasoning.

    Returns a dict with campaign data, company/contact counts,
    sequence metrics, and recent learnings.

    Args:
        campaign_slug: The campaign slug to snapshot.

    Returns:
        Dict with keys: campaign, campaign_slug, company_count, contact_count,
        sequence_metrics, recent_learnings.
    """
    # TODO: Wire up Supabase queries once DB client is available.
    # For now, return a stub structure that agents can reason about.
    logger.info("Building campaign snapshot", campaign_slug=campaign_slug)

    return {
        "campaign_slug": campaign_slug,
        "campaign": {},
        "company_count": 0,
        "contact_count": 0,
        "sequence_metrics": {
            "total_sent": 0,
            "total_opened": 0,
            "total_replied": 0,
            "total_bounced": 0,
            "open_rate": 0.0,
            "reply_rate": 0.0,
            "bounce_rate": 0.0,
        },
        "recent_learnings": [],
    }
