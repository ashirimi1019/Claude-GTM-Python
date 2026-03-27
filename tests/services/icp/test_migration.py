"""ICP migration tests."""

import pytest

from services.icp.migration import migrate_icp_profile, legacy_config_to_icp_profile


class TestMigrateIcpProfile:
    def test_v1_profile_passes_through(self):
        raw = {
            "version": 1,
            "mode": "basic",
            "strictness": {"level": "broad"},
        }
        profile = migrate_icp_profile(raw)
        assert profile.version == 1
        assert profile.mode == "basic"
        assert profile.strictness.level == "broad"

    def test_null_profile_raises(self):
        with pytest.raises(ValueError, match="null"):
            migrate_icp_profile(None)

    def test_unknown_version_raises(self):
        with pytest.raises(ValueError, match="Unknown"):
            migrate_icp_profile({"version": 99})

    def test_missing_version_defaults_to_1(self):
        raw = {"mode": "basic", "strictness": {"level": "balanced"}}
        profile = migrate_icp_profile(raw)
        assert profile.version == 1


class TestLegacyConfigToIcpProfile:
    def test_basic_conversion(self):
        legacy = {
            "strictness": "balanced",
            "min_employees": 50,
            "max_employees": 500,
        }
        profile = legacy_config_to_icp_profile(legacy)
        assert profile.strictness.level == "balanced"
        assert profile.version == 1

    def test_default_enrichment(self):
        profile = legacy_config_to_icp_profile({})
        assert profile.enrichment is not None
        assert profile.enrichment.max_contacts_per_company == 3
        assert "vp" in profile.enrichment.seniorities

    def test_invalid_strictness_defaults_to_broad(self):
        profile = legacy_config_to_icp_profile({"strictness": "invalid"})
        assert profile.strictness.level == "broad"

    def test_tech_preferences(self):
        legacy = {
            "preferred_tech": ["Python", "React"],
            "avoided_tech": ["PHP"],
        }
        profile = legacy_config_to_icp_profile(legacy)
        assert profile.scoring is not None

    def test_industry_exclusions(self):
        legacy = {"excluded_industries": ["Staffing", "Recruiting"]}
        profile = legacy_config_to_icp_profile(legacy)
        assert profile.hard_filters is not None
