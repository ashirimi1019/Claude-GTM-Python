"""Vertical playbook loader — reads .md files from context/verticals/{slug}/."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import structlog

from services.verticals.types import PLAYBOOK_FILES, VerticalPlaybook

logger = structlog.get_logger()

_DEFAULT_BASE_DIR: str | None = None


def _resolve_base_dir(base_dir: str | None = None) -> Path:
    """Resolve the verticals base directory."""
    if base_dir:
        return Path(base_dir)
    if _DEFAULT_BASE_DIR:
        return Path(_DEFAULT_BASE_DIR)
    return Path("context") / "verticals"


@lru_cache(maxsize=32)
def load_vertical_playbook(
    slug: str,
    base_dir: str | None = None,
) -> VerticalPlaybook:
    """Load all 8 playbook .md files for a vertical.

    Args:
        slug: Vertical slug (e.g. "staffing", "ai-data-consulting").
        base_dir: Override base directory for verticals. Defaults to context/verticals.

    Returns:
        VerticalPlaybook with all sections populated (empty string if file missing).
    """
    verticals_dir = _resolve_base_dir(base_dir) / slug
    sections: dict[str, str] = {}

    for field, filename in PLAYBOOK_FILES.items():
        filepath = verticals_dir / filename
        try:
            sections[field] = filepath.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            logger.warn("playbook_file_missing", slug=slug, file=filename)
            sections[field] = ""
        except OSError as exc:
            logger.error("playbook_file_read_error", slug=slug, file=filename, err=str(exc))
            sections[field] = ""

    return VerticalPlaybook(**sections)
