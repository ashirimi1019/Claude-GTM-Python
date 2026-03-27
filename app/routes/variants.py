"""Variant approval routes — Tier 3 guardrails approval queue."""

from __future__ import annotations

from fastapi import APIRouter

import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/variants", tags=["variants"])


@router.get("/pending")
async def list_pending_variants():
    """List copy variants awaiting operator approval (Tier 3 guardrails)."""
    # TODO: Query message_variants where approval_status = 'pending'
    return {"pending": []}


@router.post("/{variant_id}/approve")
async def approve_variant(variant_id: str, approved: bool = True, reason: str = ""):
    """Approve or reject a flagged copy variant.

    Args:
        variant_id: UUID of the message_variant.
        approved: True to approve, False to reject.
        reason: Optional reason for rejection.
    """
    # TODO: Update message_variant approval_status in DB
    # If approved → variant becomes available for sequences
    # If rejected → variant is archived, copy optimizer notified

    logger.info("Variant reviewed", variant_id=variant_id, approved=approved, reason=reason)
    return {
        "variant_id": variant_id,
        "status": "approved" if approved else "rejected",
        "reason": reason,
    }
