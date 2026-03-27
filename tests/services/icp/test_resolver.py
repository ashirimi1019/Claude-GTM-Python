"""Tests for services.icp.resolver."""

from services.icp.resolver import resolve_execution_config
from services.icp.types import NormalizedIcpRules


def _make_profile(strictness_level: str = "broad") -> dict:
    return {
        "version": 1,
        "mode": "basic",
        "strictness": {"level": strictness_level},
    }


def test_campaign_icp_profile_takes_priority():
    """Campaign icp_profile is ABSOLUTE source of truth."""
    campaign = {"icp_profile": _make_profile("strict")}
    offer = {"icp_profile": _make_profile("broad")}
    result = resolve_execution_config(campaign, offer)
    assert result["mode"] == "icp_builder"
    assert isinstance(result["rules"], NormalizedIcpRules)
    # Should use campaign's strict, not offer's broad
    assert result["rules"].threshold == 165  # strict threshold


def test_offer_icp_profile_used_when_campaign_is_none():
    campaign = {"icp_profile": None}
    offer = {"icp_profile": _make_profile("balanced")}
    result = resolve_execution_config(campaign, offer)
    assert result["mode"] == "icp_builder"
    assert result["rules"].threshold == 115  # balanced threshold


def test_legacy_path_when_both_profiles_none():
    campaign = {"icp_profile": None, "scoring_config_overrides": {"threshold": 100}}
    offer = {"icp_profile": None, "scoring_config_overrides": {"threshold": 200}}
    result = resolve_execution_config(campaign, offer)
    assert result["mode"] == "legacy"
    assert result["profile"] is None
    assert result["rules"] == {"threshold": 100}  # campaign overrides take priority


def test_legacy_path_fallback_to_offer_overrides():
    campaign = {"icp_profile": None}
    offer = {"icp_profile": None, "scoring_config_overrides": {"threshold": 200}}
    result = resolve_execution_config(campaign, offer)
    assert result["mode"] == "legacy"
    assert result["rules"] == {"threshold": 200}


def test_legacy_path_empty_when_no_overrides():
    campaign = {"icp_profile": None}
    offer = {"icp_profile": None}
    result = resolve_execution_config(campaign, offer)
    assert result["mode"] == "legacy"
    assert result["rules"] == {}
