"""Action executor — auto-applies safe recommendations, queues risky ones."""

from __future__ import annotations

from typing import Any

import structlog

from core.agents.types import RecommendationV2

logger = structlog.get_logger()


async def execute_actions(
    recommendations: list[RecommendationV2],
    campaign_id: str,
) -> list[dict[str, Any]]:
    """Execute agent recommendations based on risk level.

    - 'safe' risk_level: auto-applied immediately.
    - 'moderate': queued for approval.
    - 'risky': queued for approval with warning.

    Args:
        recommendations: List of recommendations to process.
        campaign_id: Campaign to apply actions to.

    Returns:
        List of execution result dicts with status and details.
    """
    results: list[dict[str, Any]] = []

    for rec in recommendations:
        if rec.risk_level == "safe":
            # Auto-apply safe actions
            outcome = await _apply_action(rec, campaign_id)
            results.append({
                "domain": rec.domain,
                "action": rec.action,
                "status": "applied",
                "outcome": outcome,
            })
        elif rec.risk_level == "moderate":
            results.append({
                "domain": rec.domain,
                "action": rec.action,
                "status": "queued_for_approval",
                "reason": "Moderate risk — requires human review",
            })
            logger.info(
                "Recommendation queued for approval",
                domain=rec.domain,
                action=rec.action,
                risk="moderate",
                campaign_id=campaign_id,
            )
        else:
            # risky
            results.append({
                "domain": rec.domain,
                "action": rec.action,
                "status": "queued_for_approval",
                "reason": "Risky action — requires human review and explicit approval",
            })
            logger.warn(
                "Risky recommendation queued",
                domain=rec.domain,
                action=rec.action,
                risk="risky",
                campaign_id=campaign_id,
            )

    applied = sum(1 for r in results if r["status"] == "applied")
    queued = sum(1 for r in results if r["status"] == "queued_for_approval")
    logger.info(
        "Action execution complete",
        campaign_id=campaign_id,
        applied=applied,
        queued=queued,
        total=len(results),
    )

    return results


async def _apply_action(rec: RecommendationV2, campaign_id: str) -> str:
    """Apply a single safe action. Returns outcome description.

    TODO: Wire up actual DB mutations per domain/action type.
    """
    logger.info(
        "Applying safe action",
        domain=rec.domain,
        action=rec.action,
        confidence=rec.confidence,
        campaign_id=campaign_id,
    )
    return f"Applied {rec.domain}/{rec.action} with confidence {rec.confidence:.2f}"
