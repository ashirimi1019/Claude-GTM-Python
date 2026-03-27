"""Lead Quality agent — detects false positives and missed opportunities."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import structlog

from core.agents.llm_reasoning import reason_about
from core.agents.types import AgentResultV2, PriorContext, RecommendationV2

logger = structlog.get_logger()

AGENT_ID = "lead-quality"
AGENT_NAME = "Lead Quality"


def _build_prompt(snapshot: dict[str, Any]) -> str:
    """Build the lead quality reasoning prompt from campaign snapshot."""
    metrics = snapshot.get("sequence_metrics", {})
    return f"""Analyze lead quality for this campaign and detect issues.

Campaign: {snapshot.get('campaign_id', 'unknown')}
Companies found: {snapshot.get('company_count', 0)}
Contacts enriched: {snapshot.get('contact_count', 0)}
Open rate: {metrics.get('open_rate', 0):.1%}
Reply rate: {metrics.get('reply_rate', 0):.1%}
Bounce rate: {metrics.get('bounce_rate', 0):.1%}
Total bounced: {metrics.get('total_bounced', 0)}

Recent learnings: {json.dumps(snapshot.get('recent_learnings', []))}

Consider:
1. Are there false positives (companies that scored high but bounced or never engaged)?
2. Are there missed opportunities (companies filtered too aggressively)?
3. Is the contact-level targeting correct (right seniority, department)?
4. Are bounce rates indicating bad data sources?

Provide recommendations in the 'lead' domain only."""


def _build_context(prior: PriorContext | None) -> str:
    """Build context string including prior agent results."""
    parts = ["You detect false positives and missed opportunities in the lead pipeline."]
    if prior and prior.prior_results:
        parts.append(f"\nPrior agent results this cycle: {len(prior.prior_results)}")
        for r in prior.prior_results:
            parts.append(f"- {r.agent_name}: {len(r.recommendations)} recommendations")
    if prior and prior.locked_domains:
        parts.append(f"\nLocked domains (do not touch): {prior.locked_domains}")
    return "\n".join(parts)


async def run_lead_quality(
    snapshot: dict[str, Any],
    prior: PriorContext | None = None,
) -> AgentResultV2:
    """Run the Lead Quality agent.

    Detects false positives and missed opportunities in the lead
    pipeline, suggesting adjustments to improve lead accuracy.
    """
    prompt = _build_prompt(snapshot)
    context = _build_context(prior)

    result = await reason_about(AGENT_NAME, prompt, context)

    recommendations = [
        RecommendationV2(**rec)
        for rec in result.get("recommendations", [])
        if rec.get("domain") == "lead"
    ]

    return AgentResultV2(
        agent_id=AGENT_ID,
        agent_name=AGENT_NAME,
        recommendations=recommendations,
        raw_reasoning=result.get("reasoning", ""),
        timestamp=datetime.now(UTC),
    )
