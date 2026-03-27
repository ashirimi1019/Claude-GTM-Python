"""Tests for services.icp.preview."""

from services.icp.preview import run_icp_preview


def _make_profile(strictness: str = "broad") -> dict:
    return {
        "version": 1,
        "mode": "basic",
        "strictness": {"level": strictness},
    }


def _make_company(
    name: str = "Acme",
    employee_count: int | None = 500,
    funding_stage: str = "series_b",
    industry: str = "technology",
    domain: str = "acme.com",
    tech_stack: list[str] | None = None,
    hiring_status: str = "likely",
    estimated_annual_revenue: float | None = 50_000_000,
    intent_topics: list[str] | None = None,
) -> dict:
    return {
        "id": name.lower().replace(" ", "-"),
        "name": name,
        "employee_count": employee_count,
        "funding_stage": funding_stage,
        "industry": industry,
        "domain": domain,
        "tech_stack": tech_stack or ["python", "react"],
        "hiring_status": hiring_status,
        "estimated_annual_revenue": estimated_annual_revenue,
        "intent_topics": intent_topics or ["cloud migration"],
    }


def test_preview_returns_expected_keys():
    result = run_icp_preview(_make_profile(), [_make_company()])
    assert "summary" in result
    assert "rejectionBreakdown" in result
    assert "topRejectionReasons" in result
    assert "tierDistribution" in result
    assert "confidenceStats" in result
    assert "scoreStats" in result
    assert "effectiveConfig" in result
    assert "sampleTraces" in result
    assert "twoStageInfo" in result


def test_preview_all_qualified_broad():
    companies = [_make_company(f"Co{i}") for i in range(3)]
    result = run_icp_preview(_make_profile("broad"), companies)
    summary = result["summary"]
    assert summary["totalCompanies"] == 3
    assert summary["qualified"] >= 1  # broad should qualify well-formed companies


def test_preview_empty_companies():
    result = run_icp_preview(_make_profile(), [])
    assert result["summary"]["totalCompanies"] == 0
    assert result["summary"]["qualified"] == 0
    assert result["summary"]["qualificationRate"] == 0.0


def test_preview_strict_rejects_more():
    companies = [
        _make_company("Good", employee_count=500, hiring_status="likely"),
        _make_company("Sparse", employee_count=None, hiring_status="unknown",
                       funding_stage="", estimated_annual_revenue=None,
                       tech_stack=[], intent_topics=[]),
    ]
    broad = run_icp_preview(_make_profile("broad"), companies)
    strict = run_icp_preview(_make_profile("very_strict"), companies)
    # very_strict should qualify fewer or equal companies vs broad
    assert strict["summary"]["qualified"] <= broad["summary"]["qualified"]


def test_preview_two_stage_info_consistent():
    companies = [_make_company(f"Co{i}") for i in range(5)]
    result = run_icp_preview(_make_profile("balanced"), companies)
    info = result["twoStageInfo"]
    assert info["stage1_input"] == 5
    assert info["stage1_qualified"] + info["stage1_rejected"] == 5
    assert info["stage2_input"] == info["stage1_qualified"]
    assert info["stage2_qualified"] + info["stage2_rejected"] == info["stage2_input"]
