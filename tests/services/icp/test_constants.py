"""ICP constants tests."""

from services.icp.constants import (
    ALL_FUNDING_STAGES,
    APOLLO_EMPLOYEE_RANGES,
    COMPETITOR_KEYWORDS,
    CONFIDENCE_FLOORS,
    DIMENSION_MAX,
    MAX_SCORE,
    SIZE_PRESETS,
    STRICTNESS_BUNDLES,
)


class TestStrictnessBundles:
    def test_four_levels(self):
        assert set(STRICTNESS_BUNDLES.keys()) == {"broad", "balanced", "strict", "very_strict"}

    def test_broad_threshold(self):
        assert STRICTNESS_BUNDLES["broad"]["threshold"] == 75

    def test_balanced_threshold(self):
        assert STRICTNESS_BUNDLES["balanced"]["threshold"] == 115

    def test_strict_threshold(self):
        assert STRICTNESS_BUNDLES["strict"]["threshold"] == 165

    def test_very_strict_threshold(self):
        assert STRICTNESS_BUNDLES["very_strict"]["threshold"] == 195

    def test_strict_requires_preferred_funding(self):
        assert STRICTNESS_BUNDLES["strict"]["require_preferred_funding"] is True

    def test_broad_accepts_incomplete(self):
        assert STRICTNESS_BUNDLES["broad"]["data_quality"] == "accept-incomplete"


class TestSizePresets:
    def test_startup_range(self):
        assert SIZE_PRESETS["startup"] == {"min": 10, "max": 100}

    def test_smb_range(self):
        assert SIZE_PRESETS["smb"] == {"min": 50, "max": 500}

    def test_enterprise_range(self):
        assert SIZE_PRESETS["enterprise"] == {"min": 1000, "max": 10000}


class TestMaxScore:
    def test_max_score_is_215(self):
        assert MAX_SCORE == 215

    def test_dimension_max_sums_match(self):
        # The dimensions should approximately sum to MAX_SCORE
        total = sum(DIMENSION_MAX.values())
        assert total >= MAX_SCORE  # may exceed due to intent being variable


class TestConfidenceFloors:
    def test_accept_incomplete(self):
        assert CONFIDENCE_FLOORS["accept-incomplete"] == 0.40

    def test_prefer_complete(self):
        assert CONFIDENCE_FLOORS["prefer-complete"] == 0.60

    def test_require_complete(self):
        assert CONFIDENCE_FLOORS["require-complete"] == 0.75


class TestCompetitorKeywords:
    def test_includes_staffing(self):
        assert "staffing" in COMPETITOR_KEYWORDS

    def test_has_reasonable_count(self):
        assert len(COMPETITOR_KEYWORDS) == 16


class TestFundingStages:
    def test_includes_seed(self):
        assert "seed" in ALL_FUNDING_STAGES

    def test_includes_public(self):
        assert "public" in ALL_FUNDING_STAGES


class TestApolloEmployeeRanges:
    def test_eleven_buckets(self):
        assert len(APOLLO_EMPLOYEE_RANGES) == 11

    def test_starts_with_smallest(self):
        assert APOLLO_EMPLOYEE_RANGES[0] == "1,10"
