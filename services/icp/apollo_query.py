"""ICP Apollo Query Builder — converts NormalizedIcpRules into Apollo search params.

Maps size rules to APOLLO_EMPLOYEE_RANGES buckets, collects tech keywords,
and flattens geography filters.
"""

from __future__ import annotations

from typing import Any

from .constants import APOLLO_EMPLOYEE_RANGES
from .types import NormalizedIcpRules


def build_apollo_query(rules: NormalizedIcpRules) -> dict[str, Any]:
    """Build Apollo organization search params from normalized ICP rules.

    Returns a dict suitable for passing to Apollo's mixed_companies/search endpoint.
    """
    params: dict[str, Any] = {}

    # Employee ranges
    employee_ranges = _map_size_to_apollo_ranges(rules)
    if employee_ranges:
        params["organization_num_employees_ranges"] = employee_ranges

    # Keywords from tech
    keywords = _collect_tech_keywords(rules)
    if keywords:
        params["q_keywords"] = keywords

    # Geography
    geo = _flatten_geography(rules)
    if geo.get("countries"):
        params["organization_locations"] = geo["countries"]
    if geo.get("us_states"):
        params["person_locations"] = geo["us_states"]

    # Industry exclusions
    hf = rules.hard_filters
    industries_cfg = hf.get("industries", {})
    excluded_industries = industries_cfg.get("excluded", [])
    if excluded_industries:
        params["organization_industry_tag_ids_exclude"] = excluded_industries

    # Funding stages from scoring
    funding_cfg = rules.scoring.get("funding", {})
    preferred = funding_cfg.get("preferred", [])
    acceptable = funding_cfg.get("acceptable", [])
    funding_stages = list(set(preferred + acceptable))
    if funding_stages:
        params["organization_latest_funding_stage_cd"] = funding_stages

    return params


def _map_size_to_apollo_ranges(rules: NormalizedIcpRules) -> list[str]:
    """Map hard_filters.company_size min/max to Apollo employee range buckets."""
    size_cfg = rules.hard_filters.get("company_size", {})
    hard_min = size_cfg.get("hard_min")
    hard_max = size_cfg.get("hard_max")

    if hard_min is None and hard_max is None:
        return []

    effective_min = hard_min or 0
    effective_max = hard_max or 999999

    matching: list[str] = []
    for bucket in APOLLO_EMPLOYEE_RANGES:
        parts = bucket.split(",")
        bucket_min = int(parts[0])
        bucket_max = int(parts[1]) if parts[1] else 999999

        # Include bucket if it overlaps with our range
        if bucket_max >= effective_min and bucket_min <= effective_max:
            matching.append(bucket)

    return matching


def _collect_tech_keywords(rules: NormalizedIcpRules) -> str:
    """Collect keywords from tech must_have + scoring preferred, limit 10."""
    keywords: list[str] = []

    # From hard filters tech must_have
    tech_hf = rules.hard_filters.get("tech", {})
    must_have = tech_hf.get("must_have", [])
    for kw in must_have:
        if kw not in keywords:
            keywords.append(kw)

    # From scoring tech preferred
    tech_scoring = rules.scoring.get("tech", {})
    preferred = tech_scoring.get("preferred", [])
    for kw in preferred:
        if kw not in keywords:
            keywords.append(kw)

    # Limit to 10
    keywords = keywords[:10]
    return " ".join(keywords) if keywords else ""


def _flatten_geography(rules: NormalizedIcpRules) -> dict[str, Any]:
    """Extract geography from hard_filters."""
    geo_cfg = rules.hard_filters.get("geography", {})
    return {
        "countries": geo_cfg.get("allowed_countries", []),
        "us_states": geo_cfg.get("allowed_us_states"),
    }
