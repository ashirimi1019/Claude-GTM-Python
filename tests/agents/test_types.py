"""Tests for agent types — 3 model validation scenarios."""

import pytest
from pydantic import ValidationError

from core.agents.types import (
    AgentResultV2,
    ConflictResolution,
    HealthContext,
    RecommendationV2,
)


def test_recommendation_valid():
    """RecommendationV2 accepts valid data."""
    rec = RecommendationV2(
        domain="icp",
        action="lower threshold to 150",
        params={"threshold": 150},
        confidence=0.85,
        reasoning="Current threshold is too strict",
        risk_level="safe",
    )
    assert rec.domain == "icp"
    assert rec.confidence == 0.85
    assert rec.risk_level == "safe"


def test_recommendation_invalid_confidence():
    """RecommendationV2 rejects confidence outside 0-1 range."""
    with pytest.raises(ValidationError):
        RecommendationV2(
            domain="icp",
            action="test",
            confidence=1.5,
            reasoning="x",
        )
    with pytest.raises(ValidationError):
        RecommendationV2(
            domain="copy",
            action="test",
            confidence=-0.1,
            reasoning="x",
        )


def test_agent_result_defaults():
    """AgentResultV2 has sensible defaults and timestamp is auto-set."""
    result = AgentResultV2(agent_id="test", agent_name="Test Agent")
    assert result.recommendations == []
    assert result.raw_reasoning == ""
    assert result.timestamp is not None

    # ConflictResolution and HealthContext also work
    cr = ConflictResolution(
        outcome="apply",
        winner_agent="a",
        loser_agent="b",
        domain="icp",
        reason="test",
    )
    assert cr.outcome == "apply"

    hc = HealthContext(bounce_rate=0.03, total_sent=100)
    assert hc.open_rate == 0.0
    assert hc.alerts == []
