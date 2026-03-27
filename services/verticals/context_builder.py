"""Context builder — assembles vertical playbook sections for a given skill."""

from __future__ import annotations

import structlog

from services.verticals.loader import load_vertical_playbook
from services.verticals.types import SKILL_PLAYBOOK_MAP

logger = structlog.get_logger()


def build_skill_context(
    skill_id: int,
    vertical_slug: str,
    base_dir: str | None = None,
) -> str:
    """Build concatenated markdown context for a skill from the vertical playbook.

    Args:
        skill_id: Skill number (1-6).
        vertical_slug: Vertical slug (e.g. "staffing").
        base_dir: Override base directory for verticals.

    Returns:
        Markdown string with relevant playbook sections.
    """
    needed = SKILL_PLAYBOOK_MAP.get(skill_id)
    if needed is None:
        logger.warn("unknown_skill_id", skill_id=skill_id)
        return ""

    playbook = load_vertical_playbook(vertical_slug, base_dir)

    sections: list[str] = []
    for field in needed:
        content = getattr(playbook, field, "")
        if content:
            header = field.replace("_", " ").title()
            sections.append(f"## {header}\n\n{content}")

    return "\n\n---\n\n".join(sections)
