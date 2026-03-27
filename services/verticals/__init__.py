"""Verticals system — playbook loading, resolution, and context building."""

from services.verticals.context_builder import build_skill_context
from services.verticals.loader import load_vertical_playbook
from services.verticals.resolver import get_effective_vertical
from services.verticals.types import SKILL_PLAYBOOK_MAP, VerticalPlaybook

__all__ = [
    "VerticalPlaybook",
    "SKILL_PLAYBOOK_MAP",
    "load_vertical_playbook",
    "get_effective_vertical",
    "build_skill_context",
]
