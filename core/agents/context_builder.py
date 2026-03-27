"""Context builder — constructs PriorContext for downstream agents."""

from __future__ import annotations

from typing import Any

from core.agents.types import AgentResultV2, HealthContext, PriorContext


def build_prior_context(
    prior_results: list[AgentResultV2],
    health: dict[str, Any],
) -> PriorContext:
    """Build PriorContext from previous agent runs for downstream agents.

    Args:
        prior_results: Results from agents that have already run this cycle.
        health: Campaign health metrics dict.

    Returns:
        PriorContext with prior results, health info, and locked domains.
    """
    # Parse health into HealthContext for validation
    health_ctx = HealthContext(**health) if health else HealthContext()

    # Determine locked domains — any domain where a high-confidence
    # recommendation was already made (confidence >= 0.8)
    locked_domains: list[str] = []
    for result in prior_results:
        for rec in result.recommendations:
            if rec.confidence >= 0.8 and rec.domain not in locked_domains:
                locked_domains.append(rec.domain)

    # Build alerts from health
    alerts: list[str] = []
    if health_ctx.bounce_rate > 0.05:
        alerts.append(f"High bounce rate: {health_ctx.bounce_rate:.1%}")
    if health_ctx.open_rate < 0.15 and health_ctx.total_sent > 50:
        alerts.append(f"Low open rate: {health_ctx.open_rate:.1%}")
    if health_ctx.reply_rate < 0.02 and health_ctx.total_sent > 100:
        alerts.append(f"Low reply rate: {health_ctx.reply_rate:.1%}")

    health_dict = health_ctx.model_dump()
    health_dict["alerts"] = alerts

    return PriorContext(
        prior_results=prior_results,
        health=health_dict,
        locked_domains=locked_domains,
    )
