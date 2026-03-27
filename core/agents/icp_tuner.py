"""ICP Tuner agent — analyzes ICP scoring results, suggests threshold/weight adjustments."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import structlog

from core.agents.llm_reasoning import reason_about
from core.agents.types import AgentResultV2, PriorContext, RecommendationV2

logger = structlog.get_logger()

AGENT_ID = "icp-tuner"
AGENT_NAME = "ICP Tuner"


def _build_prompt(snapshot: dict[str, Any]) -> str:
    """Build the ICP tuner reasoning prompt from campaign snapshot."""
    metrics = snapshot.get("sequence_metrics", {})
    return f"""Analyze the ICP scoring effectiveness for this campaign.

Campaign: {snapshot.get('campaign_id', 'unknown')}
Companies found: {snapshot.get('company_count', 0)}
Contacts enriched: {snapshot.get('contact_count', 0)}
Open rate: {metrics.get('open_rate', 0):.1%}
Reply rate: {metrics.get('reply_rate', 0):.1%}
Bounce rate: {metrics.get('bounce_rate', 0):.1%}

Recent learnings: {json.dumps(snapshot.get('recent_learnings', []))}

Consider:
1. Are scoring thresholds too strict (missing good leads) or too loose (wasting credits)?
2. Should any dimension weights be adjusted based on reply patterns?
3. Are there geography or industry filters that should change?

Provide recommendations in the 'icp' domain only."""


def _build_context(prior: PriorContext | None) -> str:
    """Build context string including prior agent results."""
    parts = ["You analyze ICP scoring configuration and suggest tuning adjustments."]
    if prior and prior.prior_results:
        parts.append(f"\nPrior agent results this cycle: {len(prior.prior_results)}")
        for r in prior.prior_results:
            parts.append(f"- {r.agent_name}: {len(r.recommendations)} recommendations")
    if prior and prior.locked_domains:
        parts.append(f"\nLocked domains (do not touch): {prior.locked_domains}")
    return "\n".join(parts)


async def run_icp_tuner(
    snapshot: dict[str, Any],
    prior: PriorContext | None = None,
) -> AgentResultV2:
    """Run the ICP Tuner agent.

    Analyzes ICP scoring results and suggests adjustments to
    thresholds, dimension weights, and filter configuration.
    """
    prompt = _build_prompt(snapshot)
    context = _build_context(prior)

    result = await reason_about(AGENT_NAME, prompt, context)

    recommendations = [
        RecommendationV2(**rec)
        for rec in result.get("recommendations", [])
        if rec.get("domain") == "icp"
    ]

    return AgentResultV2(
        agent_id=AGENT_ID,
        agent_name=AGENT_NAME,
        recommendations=recommendations,
        raw_reasoning=result.get("reasoning", ""),
        timestamp=datetime.now(UTC),
    )
