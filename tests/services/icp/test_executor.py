"""Tests for ICP Executor — hard filters, scoring, confidence, tiering, pipeline."""

from __future__ import annotations

import pytest

from services.icp.executor import (
    compute_confidence,
    compute_data_available_max,
    determine_tier,
    evaluate_hard_filters,
    execute_icp_pipeline,
    score_company_icp,
)
from services.icp.types import NormalizedIcpRules

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rules(**overrides) -> NormalizedIcpRules:
    """Build NormalizedIcpRules with convenient defaults."""
    defaults = {
        "threshold": 75.0,
        "data_quality": "accept-incomplete",
        "max_critical_unknowns": 3,
        "hard_filters": {},
        "scoring": {},
        "enrichment": {},
        "enforcement": {},
    }
    defaults.update(overrides)
    return NormalizedIcpRules(**defaults)


def _company(**overrides) -> dict:
    """Build a base company dict with sane defaults."""
    base = {
        "id": "comp-1",
        "name": "Acme Corp",
        "domain": "acme.com",
        "employee_count": 500,
        "industry": "technology",
        "funding_stage": "series_b",
        "estimated_annual_revenue": 50_000_000,
        "tech_stack": ["python", "react", "aws"],
        "hiring_status": "likely",
        "intent_topics": ["cloud migration", "data engineering"],
        "intent_score": 80,
    }
    base.update(overrides)
    return base


# ===========================================================================
# Hard Filter Tests (16 tests)
# ===========================================================================


class TestGateCompanySize:
    def test_pass_within_range(self):
        r = _rules(hard_filters={"company_size": {"hardMin": 100, "hardMax": 1000, "rejectOutside": True}})
        traces = evaluate_hard_filters(_company(employee_count=500), r)
        assert all(t.passed for t in traces)

    def test_fail_below_min(self):
        r = _rules(hard_filters={"company_size": {"hardMin": 100, "hardMax": 1000, "rejectOutside": True}})
        traces = evaluate_hard_filters(_company(employee_count=50), r)
        size_trace = traces[0]
        assert not size_trace.passed
        assert "below hardMin" in size_trace.reason

    def test_fail_above_max(self):
        r = _rules(hard_filters={"company_size": {"hardMin": 100, "hardMax": 1000, "rejectOutside": True}})
        traces = evaluate_hard_filters(_company(employee_count=2000), r)
        size_trace = traces[0]
        assert not size_trace.passed
        assert "above hardMax" in size_trace.reason

    def test_pass_when_reject_outside_false(self):
        r = _rules(hard_filters={"company_size": {"hardMin": 100, "hardMax": 200, "rejectOutside": False}})
        traces = evaluate_hard_filters(_company(employee_count=5000), r)
        assert traces[0].passed


class TestGateIndustryExcluded:
    def test_pass_not_excluded(self):
        r = _rules(hard_filters={"industries": {"excluded": ["gambling", "tobacco"], "required": []}})
        traces = evaluate_hard_filters(_company(industry="technology"), r)
        industry_trace = next(t for t in traces if t.gate == "industry_excluded")
        assert industry_trace.passed

    def test_fail_exact_match(self):
        r = _rules(hard_filters={"industries": {"excluded": ["gambling"], "required": []}})
        traces = evaluate_hard_filters(_company(industry="gambling"), r)
        industry_trace = next(t for t in traces if t.gate == "industry_excluded")
        assert not industry_trace.passed

    def test_fail_substring_match(self):
        r = _rules(hard_filters={"industries": {"excluded": ["gambling"], "required": []}})
        traces = evaluate_hard_filters(_company(industry="online gambling services"), r)
        industry_trace = next(t for t in traces if t.gate == "industry_excluded")
        assert not industry_trace.passed


class TestGateIndustryRequired:
    def test_pass_matching(self):
        r = _rules(hard_filters={"industries": {"excluded": [], "required": ["technology", "finance"]}})
        traces = evaluate_hard_filters(_company(industry="technology"), r)
        ind_trace = next(t for t in traces if t.gate == "industry_required")
        assert ind_trace.passed

    def test_fail_not_matching(self):
        r = _rules(hard_filters={"industries": {"excluded": [], "required": ["healthcare"]}})
        traces = evaluate_hard_filters(_company(industry="technology"), r)
        ind_trace = next(t for t in traces if t.gate == "industry_required")
        assert not ind_trace.passed


class TestGateFunding:
    def test_pass_no_filter(self):
        r = _rules(hard_filters={})
        traces = evaluate_hard_filters(_company(), r)
        fund_trace = next(t for t in traces if t.gate == "funding")
        assert fund_trace.passed

    def test_fail_excluded_stage(self):
        r = _rules(hard_filters={"funding": {"excluded": ["bootstrapped"], "required": []}})
        traces = evaluate_hard_filters(_company(funding_stage="bootstrapped"), r)
        fund_trace = next(t for t in traces if t.gate == "funding")
        assert not fund_trace.passed

    def test_fail_required_not_matched(self):
        r = _rules(hard_filters={"funding": {"excluded": [], "required": ["series_a", "series_b"]}})
        traces = evaluate_hard_filters(_company(funding_stage="seed"), r)
        fund_trace = next(t for t in traces if t.gate == "funding")
        assert not fund_trace.passed


class TestGateCompetitor:
    def test_pass_not_competitor(self):
        r = _rules(hard_filters={"competitors": ["staffing", "consulting"]})
        traces = evaluate_hard_filters(_company(name="Acme Corp", industry="technology"), r)
        comp_trace = next(t for t in traces if t.gate == "competitor")
        assert comp_trace.passed

    def test_fail_competitor_keyword(self):
        r = _rules(hard_filters={"competitors": ["staffing", "consulting"]})
        traces = evaluate_hard_filters(_company(name="Global Staffing Solutions", industry="staffing"), r)
        comp_trace = next(t for t in traces if t.gate == "competitor")
        assert not comp_trace.passed


class TestGateTechMustHave:
    def test_pass_all_present(self):
        r = _rules(hard_filters={"tech": {"must_have": ["python"], "behavior": "require-when-data-exists"}})
        traces = evaluate_hard_filters(_company(tech_stack=["python", "react"]), r)
        tech_trace = next(t for t in traces if t.gate == "tech_must_have")
        assert tech_trace.passed

    def test_fail_missing_tech(self):
        r = _rules(hard_filters={"tech": {"must_have": ["java"], "behavior": "require-when-data-exists"}})
        traces = evaluate_hard_filters(_company(tech_stack=["python", "react"]), r)
        tech_trace = next(t for t in traces if t.gate == "tech_must_have")
        assert not tech_trace.passed

    def test_pass_no_data_when_data_exists_behavior(self):
        r = _rules(hard_filters={"tech": {"must_have": ["java"], "behavior": "require-when-data-exists"}})
        traces = evaluate_hard_filters(_company(tech_stack=[]), r)
        tech_trace = next(t for t in traces if t.gate == "tech_must_have")
        assert tech_trace.passed

    def test_fail_no_data_require_always(self):
        r = _rules(hard_filters={"tech": {"must_have": ["java"], "behavior": "require-always"}})
        traces = evaluate_hard_filters(_company(tech_stack=[]), r)
        tech_trace = next(t for t in traces if t.gate == "tech_must_have")
        assert not tech_trace.passed


class TestGateHiringRequired:
    def test_pass_hiring_likely(self):
        r = _rules(hard_filters={"hiring_required": True})
        traces = evaluate_hard_filters(_company(hiring_status="likely"), r)
        hire_trace = next(t for t in traces if t.gate == "hiring_required")
        assert hire_trace.passed

    def test_fail_not_hiring(self):
        r = _rules(hard_filters={"hiring_required": True})
        traces = evaluate_hard_filters(_company(hiring_status="unlikely"), r)
        hire_trace = next(t for t in traces if t.gate == "hiring_required")
        assert not hire_trace.passed


class TestGateIntentRequired:
    def test_pass_has_topics(self):
        r = _rules(hard_filters={"intent_required": True})
        traces = evaluate_hard_filters(_company(intent_topics=["cloud"]), r)
        intent_trace = next(t for t in traces if t.gate == "intent_required")
        assert intent_trace.passed

    def test_fail_no_topics(self):
        r = _rules(hard_filters={"intent_required": True})
        traces = evaluate_hard_filters(_company(intent_topics=[]), r)
        intent_trace = next(t for t in traces if t.gate == "intent_required")
        assert not intent_trace.passed


# ===========================================================================
# Scoring Tests (8 tests)
# ===========================================================================


class TestScoringDimensions:
    def test_hiring_signal_likely(self):
        r = _rules(scoring={"hiringSignal": {"freshnessWeight": 1.0, "intensityWeight": 1.0}})
        trace = score_company_icp(_company(hiring_status="likely"), r)
        assert trace.dimensions["hiring_signal"] == 40.0

    def test_hiring_signal_not_likely(self):
        r = _rules(scoring={})
        trace = score_company_icp(_company(hiring_status="unlikely"), r)
        assert trace.dimensions["hiring_signal"] == 0.0

    def test_company_size_ideal(self):
        r = _rules(scoring={"company_size": {
            "ideal_min": 200, "ideal_max": 1000,
            "acceptable_max": 2000, "partial_min": 100,
        }})
        trace = score_company_icp(_company(employee_count=500), r)
        assert trace.dimensions["company_size"] == 50.0

    def test_company_size_acceptable(self):
        r = _rules(scoring={"company_size": {
            "ideal_min": 200, "ideal_max": 400,
            "acceptable_max": 2000, "partial_min": 100,
        }})
        trace = score_company_icp(_company(employee_count=500), r)
        assert trace.dimensions["company_size"] == 30.0

    def test_funding_preferred(self):
        r = _rules(scoring={"funding": {"preferred": ["series_b"], "acceptable": ["series_a"]}})
        trace = score_company_icp(_company(funding_stage="series_b"), r)
        assert trace.dimensions["funding"] == 30.0

    def test_revenue_actual(self):
        r = _rules()
        trace = score_company_icp(_company(estimated_annual_revenue=50_000_000), r)
        assert trace.dimensions["revenue"] == 20.0

    def test_tech_stack_matches(self):
        r = _rules(scoring={"techStack": {"preferred": ["python", "react"], "avoided": ["php"]}})
        trace = score_company_icp(_company(tech_stack=["python", "react"]), r)
        assert trace.dimensions["tech_stack"] == 30.0  # 15 * 2

    def test_intent_with_topics(self):
        r = _rules(scoring={})
        trace = score_company_icp(_company(intent_topics=["cloud", "data"]), r)
        assert trace.dimensions["intent"] == 25.0  # base 20 + 5 for 1 additional


class TestScoringEdgeCases:
    def test_tech_avoided_reduces_score(self):
        r = _rules(scoring={"techStack": {"preferred": ["python"], "avoided": ["php"]}})
        trace = score_company_icp(_company(tech_stack=["python", "php"]), r)
        assert trace.dimensions["tech_stack"] == 10.0  # 15 - 5

    def test_intent_below_min_score_reduction(self):
        r = _rules(scoring={"intent": {"minScore": 70, "topics": ["cloud"]}})
        co = _company(intent_topics=["cloud"], intent_score=50)
        trace = score_company_icp(co, r)
        # base 20, no additional, 60% reduction -> 20 * 0.4 = 8
        assert trace.dimensions["intent"] == 8.0


# ===========================================================================
# Confidence Tests (3 tests)
# ===========================================================================


class TestConfidence:
    def test_full_data_meets_requirement(self):
        r = _rules(data_quality="accept-incomplete", max_critical_unknowns=3)
        conf = compute_confidence(_company(), r)
        assert conf.meets_requirement is True
        assert conf.critical_unknowns == 0
        assert conf.data_completeness == pytest.approx(100.0)

    def test_missing_data_still_meets(self):
        r = _rules(data_quality="accept-incomplete", max_critical_unknowns=3)
        co = _company(tech_stack=[], funding_stage=None)
        conf = compute_confidence(co, r)
        assert conf.critical_unknowns == 2
        assert conf.meets_requirement is True  # 2 <= 3 and 4/6 >= 0.40

    def test_too_many_unknowns_fails(self):
        r = _rules(data_quality="require-complete", max_critical_unknowns=0)
        co = _company(tech_stack=[], funding_stage=None, estimated_annual_revenue=None)
        conf = compute_confidence(co, r)
        assert conf.meets_requirement is False
        assert conf.critical_unknowns == 3


# ===========================================================================
# Tier Tests (4 tests)
# ===========================================================================


class TestTierDetermination:
    def test_tier_a(self):
        assert determine_tier(150.0, 75.0) == "A"  # 150 >= 75 * 1.5

    def test_tier_b(self):
        assert determine_tier(100.0, 75.0) == "B"  # 100 >= 75, < 112.5

    def test_tier_c(self):
        assert determine_tier(55.0, 75.0) == "C"  # 55 >= 48.75, < 75

    def test_tier_none(self):
        assert determine_tier(40.0, 75.0) is None  # 40 < 48.75


# ===========================================================================
# Data Available Max Tests (2 tests)
# ===========================================================================


class TestDataAvailableMax:
    def test_full_data_max_score(self):
        r = _rules()
        co = _company()
        assert compute_data_available_max(co, r) == 215.0

    def test_missing_fields_reduce_max(self):
        r = _rules()
        co = _company(employee_count=None, tech_stack=[], funding_stage=None)
        max_score = compute_data_available_max(co, r)
        # Missing: company_size(50) + tech_stack(45) + funding(30) = 125 subtracted
        assert max_score == 215.0 - 50.0 - 45.0 - 30.0


# ===========================================================================
# Full Pipeline Tests (2 tests)
# ===========================================================================


class TestPipeline:
    def test_qualified_company(self):
        r = _rules(
            threshold=75.0,
            scoring={
                "company_size": {"ideal_min": 200, "ideal_max": 1000, "acceptable_max": 2500, "partial_min": 100},
                "funding": {"preferred": ["series_b"]},
                "techStack": {"preferred": ["python", "react"]},
            },
        )
        co = _company()
        result = execute_icp_pipeline(r, [co])
        assert len(result["qualified"]) == 1
        assert len(result["rejected"]) == 0
        trace = result["traces"][0]
        assert trace.outcome == "qualified"
        assert trace.tier is not None

    def test_rejected_by_hard_filter(self):
        r = _rules(
            hard_filters={"company_size": {"hardMin": 1000, "hardMax": 5000, "rejectOutside": True}},
        )
        co = _company(employee_count=50)
        result = execute_icp_pipeline(r, [co])
        assert len(result["qualified"]) == 0
        assert len(result["rejected"]) == 1
        trace = result["traces"][0]
        assert trace.outcome == "rejected-hard-filter"


# ===========================================================================
# Short-circuit verification
# ===========================================================================


class TestShortCircuit:
    def test_first_filter_failure_stops_evaluation(self):
        """When company_size fails, later gates should not be evaluated."""
        r = _rules(
            hard_filters={
                "company_size": {"hardMin": 1000, "hardMax": 5000, "rejectOutside": True},
                "hiring_required": True,
            },
        )
        co = _company(employee_count=50)
        traces = evaluate_hard_filters(co, r)
        # Should only have 1 trace (company_size failed, rest skipped)
        assert len(traces) == 1
        assert traces[0].gate == "company_size"
        assert not traces[0].passed
