"""Orchestrator agent — reviews all agent recommendations, suggests skill dispatch order."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import structlog

from core.agents.llm_reasoning import reason_about
from core.agents.types import AgentResultV2, RecommendationV2

logger = structlog.get_logger()

AGENT_ID = "orchestrator"
AGENT_NAME = "Orchestrator"


def _build_prompt(snapshot: dict[str, Any], agent_results: list[AgentResultV2]) -> str:
    """Build the orchestrator reasoning prompt from snapshot and agent results."""
    results_summary = []
    for r in agent_results:
        recs = [
            {"domain": rec.domain, "action": rec.action, "confidence": rec.confidence, "risk": rec.risk_level}
            for rec in r.recommendations
        ]
        results_summary.append({"agent": r.agent_name, "recommendations": recs})

    return f"""Review all agent recommendations and plan skill execution order.

Campaign: {snapshot.get('campaign_id', 'unknown')}

Agent Results:
{json.dumps(results_summary, indent=2)}

Your job:
1. Prioritize recommendations by impact and confidence
2. Resolve any remaining conflicts between agents
3. Suggest the optimal skill dispatch order (Skills 1-6)
4. Flag any recommendations that need human approval

Provide recommendations in the 'workflow' domain only."""


def _build_context(agent_results: list[AgentResultV2]) -> str:
    """Build context string from agent results."""
    parts = [
        "You are the orchestrator that coordinates all other agents.",
        f"You are reviewing {len(agent_results)} agent results.",
        "Your recommendations should be in the 'workflow' domain.",
    ]
    return "\n".join(parts)


async def run_orchestrator(
    snapshot: dict[str, Any],
    agent_results: list[AgentResultV2],
) -> AgentResultV2:
    """Run the Orchestrator agent.

    Reviews all agent recommendations and suggests the optimal
    skill dispatch order and execution plan.
    """
    prompt = _build_prompt(snapshot, agent_results)
    context = _build_context(agent_results)

    result = await reason_about(AGENT_NAME, prompt, context)

    recommendations = [
        RecommendationV2(**rec)
        for rec in result.get("recommendations", [])
        if rec.get("domain") == "workflow"
    ]

    return AgentResultV2(
        agent_id=AGENT_ID,
        agent_name=AGENT_NAME,
        recommendations=recommendations,
        raw_reasoning=result.get("reasoning", ""),
        timestamp=datetime.now(timezone.utc),
    )
