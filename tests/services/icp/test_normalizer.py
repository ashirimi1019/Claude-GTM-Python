"""Tests for the ICP normalizer service."""

from __future__ import annotations

from services.icp.constants import SIZE_PRESETS
from services.icp.normalizer import normalize_for_search_stage, normalize_icp_profile
from services.icp.types import (
    CompanySizeFilter,
    EnrichmentConfig,
    GeographyFilter,
    HardFiltersConfig,
    IcpProfile,
    ScoringConfig,
    StrictnessConfig,
    TechMustHave,
    TechStackScoring,
)


def _make_profile(**overrides) -> IcpProfile:  # type: ignore[no-untyped-def]
    """Build a minimal valid IcpProfile with sensible defaults."""
    defaults: dict = {
        "version": 1,
        "mode": "basic",
        "strictness": StrictnessConfig(level="balanced"),
        "hard_filters": HardFiltersConfig(
            company_size=CompanySizeFilter(preset="mid_market", hard_min=200, hard_max=5000),
        ),
        "scoring": ScoringConfig(
            hiring_signal={"requirement": "preferred", "freshness_weight": 0.5, "intensity_weight": 0.5},
            company_size={"ideal_min": 200, "ideal_max": 2000},
            funding={"preferred": [], "excluded": [], "acceptable": None},
            industry={"preferred": []},
            tech_stack=TechStackScoring(),
        ),
        "enrichment": EnrichmentConfig(
            seniorities=["vp", "director"],
            departments=["engineering"],
            max_contacts_per_company=3,
        ),
    }
    defaults.update(overrides)
    return IcpProfile(**defaults)


# ── Test 1: Broad strictness defaults ──


def test_broad_strictness_defaults() -> None:
    profile = _make_profile(strictness=StrictnessConfig(level="broad"))
    rules = normalize_icp_profile(profile)

    assert rules.threshold == 75
    assert rules.data_quality == "accept-incomplete"
    assert rules.max_critical_unknowns == 3
    assert rules.enforcement["level"] == "broad"
    assert rules.enforcement["is_customized"] is False


# ── Test 2: Balanced strictness produces correct threshold ──


def test_balanced_strictness_threshold() -> None:
    profile = _make_profile(strictness=StrictnessConfig(level="balanced"))
    rules = normalize_icp_profile(profile)

    assert rules.threshold == 115
    assert rules.data_quality == "prefer-complete"
    assert rules.max_critical_unknowns == 2


# ── Test 3: Balanced strictness with expert overrides ──


def test_balanced_with_expert_overrides() -> None:
    profile = _make_profile(
        strictness=StrictnessConfig(
            level="balanced",
            expert_overrides={"threshold": 190, "reject_missing_tech": True},
        ),
    )
    rules = normalize_icp_profile(profile)

    assert rules.scoring["threshold"] == 190
    assert rules.enforcement["is_customized"] is True
    # The override should apply
    assert rules.hard_filters["data_quality"]["reject_missing_tech"] is True
    # Non-overridden fields keep bundle defaults
    assert rules.hard_filters["data_quality"]["reject_missing_revenue"] is False


# ── Test 4: Size preset — startup ──


def test_size_preset_startup() -> None:
    profile = _make_profile(
        hard_filters=HardFiltersConfig(
            company_size=CompanySizeFilter(preset="startup"),
        ),
    )
    rules = normalize_icp_profile(profile)

    startup = SIZE_PRESETS["startup"]
    assert rules.scoring["company_size"]["ideal_min"] == startup["min"]
    assert rules.scoring["company_size"]["ideal_max"] == startup["max"]


# ── Test 5: Size preset — smb ──


def test_size_preset_smb() -> None:
    profile = _make_profile(
        hard_filters=HardFiltersConfig(
            company_size=CompanySizeFilter(preset="smb"),
        ),
    )
    rules = normalize_icp_profile(profile)

    smb = SIZE_PRESETS["smb"]
    assert rules.scoring["company_size"]["ideal_min"] == smb["min"]
    assert rules.scoring["company_size"]["ideal_max"] == smb["max"]


# ── Test 6: Size preset — mid_market ──


def test_size_preset_mid_market() -> None:
    profile = _make_profile(
        hard_filters=HardFiltersConfig(
            company_size=CompanySizeFilter(preset="mid_market"),
        ),
    )
    rules = normalize_icp_profile(profile)

    mm = SIZE_PRESETS["mid_market"]
    assert rules.scoring["company_size"]["ideal_min"] == mm["min"]
    assert rules.scoring["company_size"]["ideal_max"] == mm["max"]


# ── Test 7: Size preset — enterprise ──


def test_size_preset_enterprise() -> None:
    profile = _make_profile(
        hard_filters=HardFiltersConfig(
            company_size=CompanySizeFilter(preset="enterprise"),
        ),
    )
    rules = normalize_icp_profile(profile)

    ent = SIZE_PRESETS["enterprise"]
    assert rules.scoring["company_size"]["ideal_min"] == ent["min"]
    assert rules.scoring["company_size"]["ideal_max"] == ent["max"]
    # No hard_max on enterprise preset → acceptable_max = ideal_max * 2.5
    assert rules.scoring["company_size"]["acceptable_max"] == round(ent["max"] * 2.5)


# ── Test 8: Industry escalation at strict+ ──


def test_industry_escalation_at_strict() -> None:
    profile = _make_profile(
        strictness=StrictnessConfig(level="strict"),
        scoring=ScoringConfig(
            industry={"preferred": ["fintech", "healthcare"]},
            funding={"preferred": [], "excluded": [], "acceptable": None},
        ),
    )
    rules = normalize_icp_profile(profile)

    # Preferred industries should be escalated to required in hard filters
    assert "fintech" in rules.hard_filters["industries"]["required"]
    assert "healthcare" in rules.hard_filters["industries"]["required"]
    # Scoring boost multiplier should be 0.7
    assert rules.scoring["industry"]["boost_multiplier"] == 0.7
    # They should still be in scoring preferred
    assert rules.scoring["industry"]["preferred"] == ["fintech", "healthcare"]


# ── Test 9: Industry NOT escalated at balanced ──


def test_industry_not_escalated_at_balanced() -> None:
    profile = _make_profile(
        strictness=StrictnessConfig(level="balanced"),
        scoring=ScoringConfig(
            industry={"preferred": ["fintech", "healthcare"]},
            funding={"preferred": [], "excluded": [], "acceptable": None},
        ),
    )
    rules = normalize_icp_profile(profile)

    assert rules.hard_filters["industries"]["required"] == []
    assert rules.scoring["industry"]["boost_multiplier"] == 1.0


# ── Test 10: Funding escalation at strict+ ──


def test_funding_escalation_at_strict() -> None:
    profile = _make_profile(
        strictness=StrictnessConfig(level="strict"),
        scoring=ScoringConfig(
            funding={"preferred": ["series_a", "series_b"], "excluded": ["pre_seed"], "acceptable": None},
            industry={"preferred": []},
        ),
    )
    rules = normalize_icp_profile(profile)

    assert "series_a" in rules.hard_filters["funding"]["required"]
    assert "series_b" in rules.hard_filters["funding"]["required"]


# ── Test 11: Funding NOT escalated at balanced ──


def test_funding_not_escalated_at_balanced() -> None:
    profile = _make_profile(
        strictness=StrictnessConfig(level="balanced"),
        scoring=ScoringConfig(
            funding={"preferred": ["series_a", "series_b"], "excluded": ["pre_seed"], "acceptable": None},
            industry={"preferred": []},
        ),
    )
    rules = normalize_icp_profile(profile)

    assert rules.hard_filters["funding"]["required"] == []


# ── Test 12: normalize_for_search_stage forces broad ──


def test_normalize_for_search_stage_forces_broad() -> None:
    profile = _make_profile(
        strictness=StrictnessConfig(level="very_strict"),
    )
    rules = normalize_for_search_stage(profile)

    assert rules.threshold == 75  # broad threshold
    assert rules.data_quality == "accept-incomplete"
    assert rules.max_critical_unknowns == 3
    assert rules.enforcement["level"] == "broad"


# ── Test 13: Data quality mapping per strictness level ──


def test_data_quality_mapping_per_strictness() -> None:
    broad = normalize_icp_profile(_make_profile(strictness=StrictnessConfig(level="broad")))
    assert broad.hard_filters["data_quality"]["level"] == "accept-incomplete"
    assert broad.hard_filters["data_quality"]["max_critical_unknowns"] == 3

    balanced = normalize_icp_profile(_make_profile(strictness=StrictnessConfig(level="balanced")))
    assert balanced.hard_filters["data_quality"]["level"] == "prefer-complete"
    assert balanced.hard_filters["data_quality"]["max_critical_unknowns"] == 2

    strict = normalize_icp_profile(_make_profile(strictness=StrictnessConfig(level="strict")))
    assert strict.hard_filters["data_quality"]["level"] == "prefer-complete"
    assert strict.hard_filters["data_quality"]["max_critical_unknowns"] == 1

    very_strict = normalize_icp_profile(_make_profile(strictness=StrictnessConfig(level="very_strict")))
    assert very_strict.hard_filters["data_quality"]["level"] == "require-complete"
    assert very_strict.hard_filters["data_quality"]["max_critical_unknowns"] == 0


# ── Test 14: Geography filter passthrough ──


def test_geography_filter_passthrough() -> None:
    profile = _make_profile(
        hard_filters=HardFiltersConfig(
            company_size=CompanySizeFilter(preset="mid_market"),
            geography=GeographyFilter(
                allowed_countries=["US", "CA", "MX"],
                allowed_us_states=["CA", "NY", "TX"],
            ),
        ),
    )
    rules = normalize_icp_profile(profile)

    assert rules.hard_filters["geography"]["allowed_countries"] == ["US", "CA", "MX"]
    assert rules.hard_filters["geography"]["allowed_us_states"] == ["CA", "NY", "TX"]


# ── Test 15: Empty/minimal profile handling ──


def test_empty_minimal_profile() -> None:
    profile = IcpProfile()
    rules = normalize_icp_profile(profile)

    # Should use broad defaults (default strictness)
    assert rules.threshold == 75
    assert rules.data_quality == "accept-incomplete"
    assert rules.max_critical_unknowns == 3
    assert rules.hard_filters["geography"]["allowed_countries"] == []
    assert rules.hard_filters["industries"]["required"] == []
    assert rules.hard_filters["funding"]["required"] == []
    assert rules.enrichment["seniorities"] == []
    assert rules.enrichment["departments"] == []
    assert rules.enrichment["max_contacts_per_company"] == 3


# ── Test 16: Enrichment config passthrough ──


def test_enrichment_passthrough() -> None:
    profile = _make_profile(
        enrichment=EnrichmentConfig(
            seniorities=["c_suite", "vp"],
            departments=["engineering", "product"],
            max_contacts_per_company=5,
            require_verified_email=False,
        ),
    )
    rules = normalize_icp_profile(profile)

    assert rules.enrichment["seniorities"] == ["c_suite", "vp"]
    assert rules.enrichment["departments"] == ["engineering", "product"]
    assert rules.enrichment["max_contacts_per_company"] == 5
    assert rules.enrichment["require_verified_email"] is False


# ── Test 17: Funding acceptable expansion (null → all minus preferred/excluded) ──


def test_funding_acceptable_expansion() -> None:
    profile = _make_profile(
        scoring=ScoringConfig(
            funding={"preferred": ["series_a", "series_b"], "excluded": ["pre_seed"], "acceptable": None},
            industry={"preferred": []},
        ),
        hard_filters=HardFiltersConfig(
            company_size=CompanySizeFilter(preset="mid_market"),
            funding_excluded=["pre_seed"],
        ),
    )
    rules = normalize_icp_profile(profile)

    acceptable = rules.scoring["funding"]["acceptable"]
    assert "series_a" not in acceptable
    assert "series_b" not in acceptable
    assert "pre_seed" not in acceptable
    assert "seed" in acceptable
    assert "series_c" in acceptable
    assert "public" in acceptable


# ── Test 18: Competitors list is populated ──


def test_competitors_list_populated() -> None:
    profile = _make_profile()
    rules = normalize_icp_profile(profile)

    assert len(rules.hard_filters["competitors"]) > 0
    assert "staffing" in rules.hard_filters["competitors"]


# ── Test 19: Very strict data quality ──


def test_very_strict_data_quality() -> None:
    profile = _make_profile(strictness=StrictnessConfig(level="very_strict"))
    rules = normalize_icp_profile(profile)

    assert rules.threshold == 195
    assert rules.data_quality == "require-complete"
    assert rules.max_critical_unknowns == 0
    assert rules.hard_filters["data_quality"]["reject_missing_tech"] is True
    assert rules.hard_filters["data_quality"]["reject_missing_revenue"] is True


# ── Test 20: Tech must-have passthrough ──


def test_tech_must_have_passthrough() -> None:
    profile = _make_profile(
        hard_filters=HardFiltersConfig(
            company_size=CompanySizeFilter(preset="mid_market"),
            tech_must_have=TechMustHave(keywords=["python", "kubernetes"], behavior="require-always"),
        ),
    )
    rules = normalize_icp_profile(profile)

    assert rules.hard_filters["tech"]["must_have"] == ["python", "kubernetes"]
    assert rules.hard_filters["tech"]["behavior"] == "require-always"
