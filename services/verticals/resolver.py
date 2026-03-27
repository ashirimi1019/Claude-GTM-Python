"""Vertical resolver — campaign overrides offer."""

from __future__ import annotations

from app.errors import AppError


def get_effective_vertical(
    campaign_vertical_id: str | None = None,
    offer_vertical_id: str | None = None,
) -> str:
    """Resolve the effective vertical slug.

    Resolution order: campaign_vertical_id ?? offer_vertical_id.
    Raises AppError(422) if neither is set.
    """
    resolved = campaign_vertical_id or offer_vertical_id
    if not resolved:
        raise AppError(
            message="No vertical specified — set vertical on campaign or offer.",
            status_code=422,
            code="MISSING_VERTICAL",
        )
    return resolved
