"""ICP Resolver — determines execution config from campaign/offer/vertical.

INVARIANT: if campaign["icp_profile"] is not None, it is the ABSOLUTE source of truth.
"""

from __future__ import annotations

from typing import Any

from .normalizer import normalize_icp_profile
from .types import IcpProfile


def resolve_execution_config(
    campaign: dict[str, Any],
    offer: dict[str, Any],
    vertical_scoring_md: str | None = None,
) -> dict[str, Any]:
    """Resolve the execution config for a campaign.

    Returns {"mode": "icp_builder" | "legacy", "profile": ..., "rules": ...}.
    """
    # Priority 1: campaign.icp_profile (ABSOLUTE source of truth)
    icp_profile_raw = campaign.get("icp_profile")
    if icp_profile_raw is not None:
        return _build_icp_builder_result(icp_profile_raw, vertical_scoring_md)

    # Priority 2: offer.icp_profile
    icp_profile_raw = offer.get("icp_profile")
    if icp_profile_raw is not None:
        return _build_icp_builder_result(icp_profile_raw, vertical_scoring_md)

    # Priority 3: legacy path
    return _build_legacy_result(campaign, offer)


def _build_icp_builder_result(
    icp_profile_raw: dict[str, Any],
    vertical_scoring_md: str | None,
) -> dict[str, Any]:
    """Build result for ICP Builder mode."""
    profile = IcpProfile.model_validate(icp_profile_raw)
    rules = normalize_icp_profile(profile, vertical_scoring_md)
    return {
        "mode": "icp_builder",
        "profile": profile.model_dump(by_alias=True),
        "rules": rules,
    }


def _build_legacy_result(
    campaign: dict[str, Any],
    offer: dict[str, Any],
) -> dict[str, Any]:
    """Build result for legacy scoring_config_overrides path."""
    scoring_overrides = (
        campaign.get("scoring_config_overrides")
        or offer.get("scoring_config_overrides")
        or {}
    )
    return {
        "mode": "legacy",
        "profile": None,
        "rules": scoring_overrides,
    }
