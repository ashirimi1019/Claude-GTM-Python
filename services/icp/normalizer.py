"""ICP Normalizer — converts IcpProfile into NormalizedIcpRules for the executor.

The normalizer resolves strictness bundles, size presets, hard filters,
scoring dimensions, and enrichment config into a flat, executor-ready structure.
"""

from __future__ import annotations

import copy
from typing import Any

from .constants import (
    ALL_FUNDING_STAGES,
    COMPETITOR_KEYWORDS,
    SIZE_PRESETS,
    STRICTNESS_BUNDLES,
)
from .types import (
    IcpProfile,
    NormalizedIcpRules,
    StrictnessConfig,
)

# Strictness ordering for escalation checks
STRICTNESS_ORDER: dict[str, int] = {
    "broad": 0,
    "balanced": 1,
    "strict": 2,
    "very_strict": 3,
}

# Data quality level -> max critical unknowns mapping
DATA_QUALITY_TO_MAX_UNKNOWNS: dict[str, int] = {
    "accept-incomplete": 3,
    "prefer-complete": 2,
    "require-complete": 0,
}


def _resolve_strictness(
    strictness: StrictnessConfig,
) -> tuple[dict[str, Any], bool]:
    """Resolve strictness bundle with optional expert overrides.

    Returns (resolved_bundle_dict, is_customized).
    """
    bundle = dict(STRICTNESS_BUNDLES[strictness.level])
    overrides = strictness.expert_overrides

    if not overrides:
        return bundle, False

    is_customized = False

    if overrides.get("threshold") is not None:
        bundle["threshold"] = overrides["threshold"]
        is_customized = True

    if overrides.get("data_quality") is not None:
        bundle["data_quality"] = overrides["data_quality"]
        bundle["max_critical_unknowns"] = DATA_QUALITY_TO_MAX_UNKNOWNS[overrides["data_quality"]]
        is_customized = True

    if overrides.get("require_preferred_funding") is not None:
        bundle["require_preferred_funding"] = overrides["require_preferred_funding"]
        is_customized = True

    if overrides.get("require_preferred_industries") is not None:
        bundle["require_preferred_industries"] = overrides["require_preferred_industries"]
        is_customized = True

    if overrides.get("reject_missing_tech") is not None:
        bundle["reject_missing_tech"] = overrides["reject_missing_tech"]
        is_customized = True

    if overrides.get("reject_missing_revenue") is not None:
        bundle["reject_missing_revenue"] = overrides["reject_missing_revenue"]
        is_customized = True

    if overrides.get("max_critical_unknowns") is not None:
        bundle["max_critical_unknowns"] = overrides["max_critical_unknowns"]
        is_customized = True

    return bundle, is_customized


def _resolve_size_from_preset(preset: str) -> dict[str, int]:
    """Resolve a size preset name to min/max band."""
    if preset in SIZE_PRESETS:
        return dict(SIZE_PRESETS[preset])
    return dict(SIZE_PRESETS["any"])


def normalize_icp_profile(
    profile: IcpProfile,
    vertical_scoring_md: str | None = None,  # noqa: ARG001 — reserved for future vertical overrides
) -> NormalizedIcpRules:
    """Convert an IcpProfile into fully resolved NormalizedIcpRules.

    This is the main entry point for normalization. The output is consumed
    directly by the ICP executor for hard-filter gating and scoring.
    """
    resolved, is_customized = _resolve_strictness(profile.strictness)
    level = profile.strictness.level
    is_strict_plus = STRICTNESS_ORDER.get(level, 0) >= STRICTNESS_ORDER["strict"]

    # ── Hard Filters ──
    hard_filters: dict[str, Any] = {}
    hf = profile.hard_filters

    # Company size
    size_hard_min: int | None = None
    size_hard_max: int | None = None
    size_reject_outside = False
    size_preset: str | None = None
    # Track whether user explicitly set hard_min/hard_max (vs resolved from preset)
    explicit_hard_min: int | None = None
    explicit_hard_max: int | None = None

    if hf and hf.company_size:
        cs = hf.company_size
        size_preset = cs.preset
        explicit_hard_min = cs.hard_min
        explicit_hard_max = cs.hard_max
        if cs.preset and cs.preset in SIZE_PRESETS:
            preset_band = _resolve_size_from_preset(cs.preset)
            size_hard_min = cs.hard_min if cs.hard_min is not None else preset_band["min"]
            size_hard_max = cs.hard_max if cs.hard_max is not None else preset_band["max"]
        else:
            size_hard_min = cs.hard_min
            size_hard_max = cs.hard_max
        size_reject_outside = cs.reject_outside

    hard_filters["company_size"] = {
        "hard_min": size_hard_min,
        "hard_max": size_hard_max,
        "reject_outside": size_reject_outside,
        "preset": size_preset,
    }

    # Industry
    industry_excluded: list[str] = []
    industry_required_from_profile: list[str] = []
    industry_preferred: list[str] = []

    if hf:
        industry_excluded = list(hf.industry_excluded or [])
        industry_required_from_profile = list(hf.industry_required or [])

    # Scoring-level industry preferred
    if profile.scoring and profile.scoring.industry:
        industry_preferred = list(profile.scoring.industry.get("preferred", []))

    # Industry escalation: at strict+, preferred industries become required
    industry_required = list(industry_required_from_profile)
    if is_strict_plus and resolved["require_preferred_industries"] and industry_preferred:
        # Merge preferred into required (dedup)
        existing = set(industry_required)
        for ind in industry_preferred:
            if ind not in existing:
                industry_required.append(ind)

    hard_filters["industries"] = {
        "excluded": industry_excluded,
        "required": industry_required,
    }

    # Funding
    funding_excluded: list[str] = []
    funding_required_from_profile: list[str] = []
    funding_preferred: list[str] = []

    if hf:
        funding_excluded = list(hf.funding_excluded or [])
        funding_required_from_profile = list(hf.funding_required or [])

    if profile.scoring and profile.scoring.funding:
        funding_preferred = list(profile.scoring.funding.get("preferred", []))

    # Funding escalation: at strict+, preferred funding becomes required
    funding_required = list(funding_required_from_profile)
    if is_strict_plus and resolved["require_preferred_funding"] and funding_preferred:
        existing = set(funding_required)
        for f in funding_preferred:
            if f not in existing:
                funding_required.append(f)

    hard_filters["funding"] = {
        "excluded": funding_excluded,
        "required": funding_required,
    }

    # Competitors
    hard_filters["competitors"] = list(COMPETITOR_KEYWORDS)

    # Tech must-have
    tech_must_have_keywords: list[str] = []
    tech_must_have_behavior = "require-when-data-exists"
    if hf and hf.tech_must_have:
        tech_must_have_keywords = list(hf.tech_must_have.keywords)
        tech_must_have_behavior = hf.tech_must_have.behavior

    hard_filters["tech"] = {
        "must_have": tech_must_have_keywords,
        "behavior": tech_must_have_behavior,
    }

    # Hiring / Intent required
    hard_filters["hiring_required"] = bool(hf.hiring_required) if hf and hf.hiring_required is not None else False
    hard_filters["intent_required"] = bool(hf.intent_required) if hf and hf.intent_required is not None else False

    # Geography
    geo_countries: list[str] = []
    geo_us_states: list[str] | None = None
    if hf and hf.geography:
        geo_countries = list(hf.geography.allowed_countries)
        geo_us_states = list(hf.geography.allowed_us_states) if hf.geography.allowed_us_states else None

    hard_filters["geography"] = {
        "allowed_countries": geo_countries,
        "allowed_us_states": geo_us_states,
    }

    # Data quality
    hard_filters["data_quality"] = {
        "reject_missing_tech": resolved["reject_missing_tech"],
        "reject_missing_revenue": resolved["reject_missing_revenue"],
        "max_critical_unknowns": resolved["max_critical_unknowns"],
        "level": resolved["data_quality"],
    }

    # ── Scoring ──
    scoring: dict[str, Any] = {}

    # Threshold
    scoring["threshold"] = resolved["threshold"]

    # Company size scoring bands
    ideal_min = size_hard_min or 1
    ideal_max = size_hard_max or 100000
    if hf and hf.company_size and hf.company_size.preset and hf.company_size.preset in SIZE_PRESETS:
        preset_band = SIZE_PRESETS[hf.company_size.preset]
        ideal_min = preset_band["min"]
        ideal_max = preset_band["max"]

    partial_min = explicit_hard_min if explicit_hard_min is not None else 0
    acceptable_max = explicit_hard_max if explicit_hard_max is not None else round(ideal_max * 2.5)

    scoring["company_size"] = {
        "ideal_min": ideal_min,
        "ideal_max": ideal_max,
        "acceptable_max": acceptable_max,
        "partial_min": partial_min,
    }

    # Funding scoring
    funding_acceptable: list[str] = []
    if profile.scoring and profile.scoring.funding:
        fund_data = profile.scoring.funding
        funding_preferred = list(fund_data.get("preferred", []))
        explicit_acceptable = fund_data.get("acceptable")
        if explicit_acceptable is not None:
            funding_acceptable = list(explicit_acceptable)
        else:
            pref_set = set(funding_preferred)
            excl_set = set(funding_excluded)
            funding_acceptable = [s for s in ALL_FUNDING_STAGES if s not in pref_set and s not in excl_set]
    else:
        funding_acceptable = list(ALL_FUNDING_STAGES)

    scoring["funding"] = {
        "preferred": funding_preferred,
        "acceptable": funding_acceptable,
    }

    # Revenue scoring
    revenue_minimum = 0
    revenue_infer = False
    if profile.scoring and profile.scoring.revenue:
        revenue_minimum = profile.scoring.revenue.get("minimum", 0)
        revenue_infer = profile.scoring.revenue.get("infer_from_employees", False)

    scoring["revenue"] = {
        "minimum": revenue_minimum,
        "infer_from_employees": revenue_infer,
    }

    # Hiring signal scoring
    hiring_signal_data: dict[str, Any] = {}
    freshness_weight = 0.5
    intensity_weight = 0.5
    hiring_requirement = "preferred"

    if profile.scoring and profile.scoring.hiring_signal:
        hs = profile.scoring.hiring_signal
        freshness_weight = hs.get("freshness_weight", 0.5)
        intensity_weight = hs.get("intensity_weight", 0.5)
        hiring_requirement = hs.get("requirement", "preferred")

    hiring_signal_data = {
        "requirement": hiring_requirement,
        "freshness_weight": freshness_weight,
        "intensity_weight": intensity_weight,
    }
    scoring["hiring_signal"] = hiring_signal_data

    # Tech scoring
    tech_preferred: list[str] = []
    tech_nice_to_have: list[str] = []
    tech_avoided: list[str] = []
    tech_weights: dict[str, float] = {}

    if profile.scoring and profile.scoring.tech_stack:
        ts = profile.scoring.tech_stack
        tech_preferred = list(ts.preferred)
        tech_nice_to_have = list(ts.nice_to_have)
        tech_avoided = list(ts.avoided)
        if ts.weights:
            tech_weights = dict(ts.weights)
        else:
            for t in tech_preferred + tech_nice_to_have:
                tech_weights[t] = 1.0

    scoring["tech"] = {
        "preferred": tech_preferred + tech_nice_to_have,
        "avoided": tech_avoided,
        "weights": tech_weights,
    }

    # Industry scoring (with boost multiplier for strict+ escalation)
    boost_multiplier = 0.7 if (is_strict_plus and resolved["require_preferred_industries"]) else 1.0

    scoring["industry"] = {
        "preferred": industry_preferred,
        "boost_multiplier": boost_multiplier,
    }

    # Domain scoring
    scoring["domain"] = {
        "preferred": [],
    }

    # Intent scoring
    intent_topics: list[str] = []
    intent_min_score = 50.0
    intent_requirement = "ignored"
    if profile.scoring and profile.scoring.intent:
        intent_topics = list(profile.scoring.intent.topics)
        intent_min_score = profile.scoring.intent.min_score

    scoring["intent"] = {
        "topics": intent_topics,
        "min_score": intent_min_score,
        "requirement": intent_requirement,
    }

    # ── Enrichment ──
    enrichment: dict[str, Any] = {}
    if profile.enrichment:
        enrichment = {
            "seniorities": list(profile.enrichment.seniorities),
            "departments": list(profile.enrichment.departments),
            "max_contacts_per_company": profile.enrichment.max_contacts_per_company,
            "require_verified_email": profile.enrichment.require_verified_email,
        }
    else:
        enrichment = {
            "seniorities": [],
            "departments": [],
            "max_contacts_per_company": 3,
            "require_verified_email": True,
        }

    # ── Build result ──
    return NormalizedIcpRules(
        threshold=resolved["threshold"],
        data_quality=resolved["data_quality"],
        max_critical_unknowns=resolved["max_critical_unknowns"],
        hard_filters=hard_filters,
        scoring=scoring,
        enrichment=enrichment,
        enforcement={
            "level": level,
            "is_customized": is_customized,
        },
    )


def normalize_for_search_stage(
    profile: IcpProfile,
    vertical_scoring_md: str | None = None,
) -> NormalizedIcpRules:
    """Produce search-stage rules from an IcpProfile.

    Forces BROAD strictness while preserving all ICP dimensions.
    Used for Stage 1 of two-stage pipeline (high recall against sparse Apollo data).
    """
    search_profile = copy.deepcopy(profile)
    search_profile.strictness = StrictnessConfig(level="broad", expert_overrides=None)
    return normalize_icp_profile(search_profile, vertical_scoring_md)
