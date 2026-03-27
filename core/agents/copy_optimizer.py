"""Copy Optimizer agent — analyzes email variant performance, suggests copy changes."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import structlog

from core.agents.llm_reasoning import reason_about
from core.agents.types import AgentResultV2, PriorContext, RecommendationV2

logger = structlog.get_logger()

AGENT_ID = "copy-optimizer"
AGENT_NAME = "Copy Optimizer"


def _build_prompt(snapshot: dict[str, Any]) -> str:
    """Build the copy optimizer reasoning prompt from campaign snapshot."""
    metrics = snapshot.get("sequence_metrics", {})
    return f"""Analyze email and LinkedIn copy performance for this campaign.

Campaign: {snapshot.get('campaign_id', 'unknown')}
Total sent: {metrics.get('total_sent', 0)}
Open rate: {metrics.get('open_rate', 0):.1%}
Reply rate: {metrics.get('reply_rate', 0):.1%}
Bounce rate: {metrics.get('bounce_rate', 0):.1%}

Recent learnings: {json.dumps(snapshot.get('recent_learnings', []))}

Consider:
1. Which subject lines are performing best/worst?
2. Should email length, tone, or CTA be adjusted?
3. Are personalization hooks landing or falling flat?
4. LinkedIn copy effectiveness vs email?

Provide recommendations in the 'copy' domain only."""


def _build_context(prior: PriorContext | None) -> str:
    """Build context string including prior agent results."""
    parts = ["You optimize outbound email and LinkedIn copy for higher engagement."]
    if prior and prior.prior_results:
        parts.append(f"\nPrior agent results this cycle: {len(prior.prior_results)}")
        for r in prior.prior_results:
            parts.append(f"- {r.agent_name}: {len(r.recommendations)} recommendations")
    if prior and prior.locked_domains:
        parts.append(f"\nLocked domains (do not touch): {prior.locked_domains}")
    return "\n".join(parts)


async def run_copy_optimizer(
    snapshot: dict[str, Any],
    prior: PriorContext | None = None,
) -> AgentResultV2:
    """Run the Copy Optimizer agent.

    Analyzes email variant performance and suggests copy changes
    to improve open rates, reply rates, and engagement.
    """
    prompt = _build_prompt(snapshot)
    context = _build_context(prior)

    result = await reason_about(AGENT_NAME, prompt, context)

    recommendations = [
        RecommendationV2(**rec)
        for rec in result.get("recommendations", [])
        if rec.get("domain") == "copy"
    ]

    return AgentResultV2(
        agent_id=AGENT_ID,
        agent_name=AGENT_NAME,
        recommendations=recommendations,
        raw_reasoning=result.get("reasoning", ""),
        timestamp=datetime.now(UTC),
    )
