"""Tests for context_builder — 3 scenarios."""

from core.agents.context_builder import build_prior_context
from core.agents.types import AgentResultV2, RecommendationV2


def test_empty_input():
    """Empty prior results and health produces a clean PriorContext."""
    ctx = build_prior_context(prior_results=[], health={})
    assert ctx.prior_results == []
    assert ctx.locked_domains == []
    assert ctx.health["bounce_rate"] == 0.0
    assert ctx.health["total_sent"] == 0


def test_with_prior_results():
    """Prior results populate the context and trigger health alerts."""
    result = AgentResultV2(
        agent_id="icp-tuner",
        agent_name="ICP Tuner",
        recommendations=[
            RecommendationV2(
                domain="icp",
                action="lower threshold",
                confidence=0.85,
                reasoning="Threshold too strict",
            ),
        ],
    )
    health = {
        "bounce_rate": 0.08,
        "open_rate": 0.10,
        "reply_rate": 0.01,
        "total_sent": 200,
    }
    ctx = build_prior_context(prior_results=[result], health=health)

    assert len(ctx.prior_results) == 1
    assert ctx.prior_results[0].agent_id == "icp-tuner"
    # High bounce rate alert
    assert any("bounce" in a.lower() for a in ctx.health["alerts"])
    # Low open rate alert
    assert any("open" in a.lower() for a in ctx.health["alerts"])
    # Low reply rate alert
    assert any("reply" in a.lower() for a in ctx.health["alerts"])


def test_locked_domains():
    """High-confidence recommendations lock their domain."""
    results = [
        AgentResultV2(
            agent_id="icp-tuner",
            agent_name="ICP Tuner",
            recommendations=[
                RecommendationV2(domain="icp", action="a", confidence=0.9, reasoning="x"),
            ],
        ),
        AgentResultV2(
            agent_id="copy-optimizer",
            agent_name="Copy Optimizer",
            recommendations=[
                RecommendationV2(domain="copy", action="b", confidence=0.5, reasoning="y"),
            ],
        ),
    ]
    ctx = build_prior_context(prior_results=results, health={})

    # icp locked (0.9 >= 0.8), copy not locked (0.5 < 0.8)
    assert "icp" in ctx.locked_domains
    assert "copy" not in ctx.locked_domains
