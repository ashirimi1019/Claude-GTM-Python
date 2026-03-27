"""Artifacts routes — skill run output management."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Query

from app.config import get_settings
from app.errors import AppError

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("")
async def list_artifacts(
    offer_slug: str = Query(...),
    campaign_slug: str | None = Query(None),
):
    """List all artifacts (output files) for an offer/campaign."""
    settings = get_settings()
    offers_root = Path(settings.offers_dir).resolve()
    base = (offers_root / offer_slug).resolve()

    if campaign_slug:
        base = (base / "campaigns" / campaign_slug).resolve()

    # Path traversal protection
    if not base.is_relative_to(offers_root):
        return {"artifacts": []}

    if not base.exists():
        return {"artifacts": []}

    artifacts = []
    for path in base.rglob("*"):
        if path.is_file():
            artifacts.append({
                "name": path.name,
                "path": str(path.relative_to(offers_root)),
                "size_bytes": path.stat().st_size,
                "type": path.suffix.lstrip("."),
            })

    return {"artifacts": artifacts}


@router.get("/{artifact_path:path}")
async def get_artifact(artifact_path: str):
    """Read a specific artifact file."""
    settings = get_settings()
    offers_dir = Path(settings.offers_dir).resolve()
    filepath = (offers_dir / artifact_path).resolve()

    if not filepath.is_relative_to(offers_dir):
        raise AppError(
            message="Invalid artifact path",
            status_code=400,
            code="BAD_REQUEST",
        )

    if not filepath.exists():
        raise AppError(
            message=f"Artifact not found: {artifact_path}",
            status_code=404,
            code="NOT_FOUND",
        )

    if filepath.suffix == ".json":
        return json.loads(filepath.read_text(encoding="utf-8"))
    elif filepath.suffix in (".md", ".txt", ".csv"):
        return {"content": filepath.read_text(encoding="utf-8"), "type": filepath.suffix}
    else:
        raise AppError(
            message=f"Unsupported artifact type: {filepath.suffix}",
            status_code=400,
            code="UNSUPPORTED_TYPE",
        )
