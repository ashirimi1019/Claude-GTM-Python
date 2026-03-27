"""Conflict detector — resolves domain conflicts between agent recommendations."""

from __future__ import annotations

from core.agents.types import AgentResultV2, ConflictResolution

# Higher index = higher precedence
AGENT_PRECEDENCE: dict[str, int] = {
    "orchestrator": 0,
    "copy-optimizer": 1,
    "icp-tuner": 2,
    "lead-quality": 3,
}


def detect_conflicts(results: list[AgentResultV2]) -> list[ConflictResolution]:
    """Detect and resolve conflicts between agent recommendations.

    Rules:
    - Intra-agent: only the highest-confidence recommendation per domain survives.
    - Cross-agent: higher-precedence agent wins on same domain.

    Domain precedence: lead-quality > icp-tuner > copy-optimizer > orchestrator

    Returns:
        List of ConflictResolution objects describing suppressed recommendations.
    """
    resolutions: list[ConflictResolution] = []

    # Phase 1: Intra-agent dedup — keep highest confidence per domain per agent
    for result in results:
        domain_best: dict[str, tuple[int, float]] = {}  # domain -> (index, confidence)
        for i, rec in enumerate(result.recommendations):
            existing = domain_best.get(rec.domain)
            if existing is None or rec.confidence > existing[1]:
                if existing is not None:
                    resolutions.append(
                        ConflictResolution(
                            outcome="suppress",
                            winner_agent=result.agent_id,
                            loser_agent=result.agent_id,
                            domain=rec.domain,
                            reason=f"Intra-agent dedup: kept higher confidence ({rec.confidence:.2f} > {existing[1]:.2f})",
                        )
                    )
                domain_best[rec.domain] = (i, rec.confidence)
            else:
                resolutions.append(
                    ConflictResolution(
                        outcome="suppress",
                        winner_agent=result.agent_id,
                        loser_agent=result.agent_id,
                        domain=rec.domain,
                        reason=f"Intra-agent dedup: kept higher confidence ({existing[1]:.2f} >= {rec.confidence:.2f})",
                    )
                )

    # Phase 2: Cross-agent conflicts — same domain, different agents
    # Collect best recommendation per domain per agent
    agent_domain_map: dict[str, list[tuple[str, int]]] = {}  # domain -> [(agent_id, precedence)]
    for result in results:
        seen_domains: set[str] = set()
        for rec in result.recommendations:
            if rec.domain not in seen_domains:
                seen_domains.add(rec.domain)
                prec = AGENT_PRECEDENCE.get(result.agent_id, -1)
                agent_domain_map.setdefault(rec.domain, []).append((result.agent_id, prec))

    for domain, agents in agent_domain_map.items():
        if len(agents) <= 1:
            continue
        # Sort by precedence descending — highest precedence wins
        agents_sorted = sorted(agents, key=lambda x: x[1], reverse=True)
        winner_id = agents_sorted[0][0]
        for loser_id, _ in agents_sorted[1:]:
            resolutions.append(
                ConflictResolution(
                    outcome="suppress",
                    winner_agent=winner_id,
                    loser_agent=loser_id,
                    domain=domain,
                    reason=f"Cross-agent: {winner_id} has higher precedence than {loser_id} on domain '{domain}'",
                )
            )

    return resolutions
