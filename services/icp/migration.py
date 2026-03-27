"""ICP profile migration — version routing and legacy config conversion."""

from __future__ import annotations

from typing import Any

from services.icp.types import EnrichmentConfig, IcpProfile, StrictnessConfig


def migrate_icp_profile(raw: dict[str, Any] | None) -> IcpProfile:
    """Route an ICP profile through version migrations.

    Args:
        raw: Raw JSON dict from database icp_profile column.

    Returns:
        Validated IcpProfile at current version.

    Raises:
        ValueError: If version is unknown or profile is null.
    """
    if raw is None:
        raise ValueError("Cannot migrate null ICP profile")

    version = raw.get("version", 1)

    if version == 1:
        return IcpProfile.model_validate(raw)
    else:
        raise ValueError(f"Unknown ICP profile version: {version}")


def legacy_config_to_icp_profile(legacy: dict[str, Any]) -> IcpProfile:
    """Convert legacy ScoringConfigOverrides to IcpProfile v1.

    Used when a campaign/offer has scoring_config_overrides but no icp_profile.

    Args:
        legacy: scoring_config_overrides dict from database.

    Returns:
        IcpProfile v1 with equivalent configuration.
    """
    strictness_level = legacy.get("strictness", "broad")
    if strictness_level not in ("broad", "balanced", "strict", "very_strict"):
        strictness_level = "broad"

    # Build hard filters from legacy
    hard_filters: dict[str, Any] = {}

    if "min_employees" in legacy or "max_employees" in legacy:
        hard_filters["company_size"] = {
            "hardMin": legacy.get("min_employees"),
            "hardMax": legacy.get("max_employees"),
            "rejectOutside": legacy.get("reject_outside_size", False),
        }

    if "excluded_industries" in legacy:
        hard_filters["industry_excluded"] = legacy["excluded_industries"]

    if "competitor_detection" in legacy:
        hard_filters["competitor"] = legacy["competitor_detection"]

    # Build scoring from legacy
    scoring: dict[str, Any] = {}

    if "preferred_funding" in legacy:
        scoring["funding"] = {
            "preferred": legacy["preferred_funding"],
            "acceptable": legacy.get("acceptable_funding", []),
        }

    if "preferred_tech" in legacy:
        scoring["techStack"] = {
            "preferred": legacy["preferred_tech"],
            "niceToHave": legacy.get("nice_to_have_tech", []),
            "avoided": legacy.get("avoided_tech", []),
        }

    if "preferred_industries" in legacy:
        scoring["industry"] = {
            "preferred": legacy["preferred_industries"],
        }

    # Default enrichment config
    enrichment = EnrichmentConfig(
        seniorities=["vp", "director", "head"],
        departments=["engineering", "data"],
        max_contacts_per_company=3,
        require_verified_email=True,
    )

    return IcpProfile(
        version=1,
        mode="basic",
        strictness=StrictnessConfig(level=strictness_level),
        hard_filters=hard_filters if hard_filters else None,
        scoring=scoring if scoring else None,
        enrichment=enrichment,
    )
