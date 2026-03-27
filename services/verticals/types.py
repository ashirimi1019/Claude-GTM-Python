"""Vertical playbook types and skill-to-playbook mapping."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VerticalPlaybook:
    """All 8 playbook sections for a vertical."""

    overview: str
    icp: str
    buyers: str
    signals: str
    scoring: str
    messaging: str
    objections: str
    proof_points: str


PLAYBOOK_FILES: dict[str, str] = {
    "overview": "overview.md",
    "icp": "icp.md",
    "buyers": "buyers.md",
    "signals": "signals.md",
    "scoring": "scoring.md",
    "messaging": "messaging.md",
    "objections": "objections.md",
    "proof_points": "proof-points.md",
}

# Which playbook files each skill needs
SKILL_PLAYBOOK_MAP: dict[int, list[str]] = {
    1: ["overview", "icp", "buyers"],
    2: ["overview", "icp", "buyers", "signals", "messaging"],
    3: ["messaging", "objections", "proof_points"],
    4: ["icp", "scoring", "signals"],
    5: ["messaging", "proof_points"],
    6: ["overview", "messaging"],
}
