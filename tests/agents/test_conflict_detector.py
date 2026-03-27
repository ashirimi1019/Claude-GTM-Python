"""Tests for conflict_detector — 5 scenarios."""

from core.agents.conflict_detector import detect_conflicts
from core.agents.types import AgentResultV2, RecommendationV2


def _make_result(agent_id: str, agent_name: str, recs: list[dict]) -> AgentResultV2:
    """Helper to build AgentResultV2 with recommendations."""
    return AgentResultV2(
        agent_id=agent_id,
        agent_name=agent_name,
        recommendations=[RecommendationV2(**r) for r in recs],
    )


def test_no_conflicts_when_different_domains():
    """No conflicts when each agent operates on a different domain."""
    results = [
        _make_result("icp-tuner", "ICP Tuner", [
            {"domain": "icp", "action": "lower threshold", "confidence": 0.8, "reasoning": "x"},
        ]),
        _make_result("copy-optimizer", "Copy Optimizer", [
            {"domain": "copy", "action": "shorten subject", "confidence": 0.7, "reasoning": "y"},
        ]),
    ]
    resolutions = detect_conflicts(results)
    # No cross-agent conflicts (domains are different)
    cross = [r for r in resolutions if r.winner_agent != r.loser_agent]
    assert len(cross) == 0


def test_same_domain_conflict_resolved_by_precedence():
    """When two agents touch the same domain, higher precedence wins."""
    results = [
        _make_result("icp-tuner", "ICP Tuner", [
            {"domain": "lead", "action": "adjust filters", "confidence": 0.6, "reasoning": "x"},
        ]),
        _make_result("lead-quality", "Lead Quality", [
            {"domain": "lead", "action": "flag false positives", "confidence": 0.9, "reasoning": "y"},
        ]),
    ]
    resolutions = detect_conflicts(results)
    cross = [r for r in resolutions if r.winner_agent != r.loser_agent]
    assert len(cross) == 1
    assert cross[0].winner_agent == "lead-quality"
    assert cross[0].loser_agent == "icp-tuner"
    assert cross[0].domain == "lead"


def test_precedence_order():
    """Verify full precedence chain: lead-quality > icp-tuner > copy-optimizer > orchestrator."""
    # All agents claim the same domain
    results = [
        _make_result("orchestrator", "Orchestrator", [
            {"domain": "workflow", "action": "a1", "confidence": 0.9, "reasoning": "x"},
        ]),
        _make_result("copy-optimizer", "Copy Optimizer", [
            {"domain": "workflow", "action": "a2", "confidence": 0.9, "reasoning": "x"},
        ]),
        _make_result("icp-tuner", "ICP Tuner", [
            {"domain": "workflow", "action": "a3", "confidence": 0.9, "reasoning": "x"},
        ]),
        _make_result("lead-quality", "Lead Quality", [
            {"domain": "workflow", "action": "a4", "confidence": 0.9, "reasoning": "x"},
        ]),
    ]
    resolutions = detect_conflicts(results)
    cross = [r for r in resolutions if r.winner_agent != r.loser_agent]
    # lead-quality should win all cross-agent conflicts on 'workflow'
    assert all(r.winner_agent == "lead-quality" for r in cross)
    # 3 losers: orchestrator, copy-optimizer, icp-tuner
    losers = {r.loser_agent for r in cross}
    assert losers == {"orchestrator", "copy-optimizer", "icp-tuner"}


def test_intra_agent_dedup():
    """When one agent has multiple recs for the same domain, keep highest confidence."""
    results = [
        _make_result("icp-tuner", "ICP Tuner", [
            {"domain": "icp", "action": "lower threshold", "confidence": 0.5, "reasoning": "x"},
            {"domain": "icp", "action": "raise threshold", "confidence": 0.9, "reasoning": "y"},
        ]),
    ]
    resolutions = detect_conflicts(results)
    intra = [r for r in resolutions if r.winner_agent == r.loser_agent]
    assert len(intra) == 1
    assert intra[0].domain == "icp"
    assert intra[0].outcome == "suppress"


def test_all_clear_empty_results():
    """No conflicts when no agent results are provided."""
    resolutions = detect_conflicts([])
    assert resolutions == []
