"""Agent memory — persists learnings to JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


MAX_MEMORY_ENTRIES = 1000


def save_agent_memory(
    learnings: list[dict[str, Any]],
    filepath: str = "context/learnings/agent-memory.json",
    max_entries: int = MAX_MEMORY_ENTRIES,
) -> None:
    """Persist agent learnings to a JSON file.

    Appends new learnings to existing file content. Creates the file
    and parent directories if they don't exist. Trims oldest entries
    when the list exceeds *max_entries*.

    Args:
        learnings: List of learning dicts to persist.
        filepath: Path to the JSON file (relative to project root).
        max_entries: Maximum entries to retain (oldest trimmed first).
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing: list[dict[str, Any]] = []
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warn("Could not read existing agent memory, starting fresh", error=str(e))

    existing.extend(learnings)

    # Trim from the front (oldest entries) when exceeding max
    if len(existing) > max_entries:
        trimmed = len(existing) - max_entries
        existing = existing[-max_entries:]
        logger.info("Agent memory trimmed", trimmed=trimmed, remaining=len(existing))

    path.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")
    logger.info("Agent memory saved", filepath=filepath, total_learnings=len(existing))
