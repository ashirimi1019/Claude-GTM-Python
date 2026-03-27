"""Agent memory — persists learnings to JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


def save_agent_memory(
    learnings: list[dict[str, Any]],
    filepath: str = "context/learnings/agent-memory.json",
) -> None:
    """Persist agent learnings to a JSON file.

    Appends new learnings to existing file content. Creates the file
    and parent directories if they don't exist.

    Args:
        learnings: List of learning dicts to persist.
        filepath: Path to the JSON file (relative to project root).
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

    path.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")
    logger.info("Agent memory saved", filepath=filepath, total_learnings=len(existing))
