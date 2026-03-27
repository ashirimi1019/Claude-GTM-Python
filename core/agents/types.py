"""Agent system type definitions — v2 multi-agent coordination."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class RecommendationV2(BaseModel):
    """A single actionable recommendation from an agent."""

    domain: Literal["icp", "copy", "lead", "workflow"]
    action: str
    params: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
    risk_level: Literal["safe", "moderate", "risky"] = "safe"


class AgentResultV2(BaseModel):
    """Output from an agent run."""

    agent_id: str
    agent_name: str
    recommendations: list[RecommendationV2] = Field(default_factory=list)
    raw_reasoning: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HealthContext(BaseModel):
    """Campaign health metrics for agent reasoning."""

    bounce_rate: float = 0.0
    open_rate: float = 0.0
    reply_rate: float = 0.0
    total_sent: int = 0
    alerts: list[str] = Field(default_factory=list)


class PriorContext(BaseModel):
    """Context from previous agent runs, passed to downstream agents."""

    prior_results: list[AgentResultV2] = Field(default_factory=list)
    health: dict[str, Any] = Field(default_factory=dict)
    locked_domains: list[str] = Field(default_factory=list)


class ConflictResolution(BaseModel):
    """Resolution of a conflict between two agent recommendations."""

    outcome: Literal["apply", "suppress", "defer"]
    winner_agent: str
    loser_agent: str
    domain: str
    reason: str
