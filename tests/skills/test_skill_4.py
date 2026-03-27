"""Tests for Skill 4 — Find Leads."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from clients.apollo.types import ApolloCompany, ApolloContact, ApolloSearchResponse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_company(name: str, domain: str, country: str = "United States", **kw) -> dict:
    return {
        "id": f"id-{name}",
        "name": name,
        "domain": domain,
        "country": country,
        "employee_count": kw.get("employee_count", 200),
        "industry": kw.get("industry", "Technology"),
        "funding_stage": kw.get("funding_stage", "Series B"),
        "estimated_annual_revenue": kw.get("estimated_annual_revenue"),
        "tech_stack": kw.get("tech_stack", ["Python", "AWS"]),
        "hiring_status": kw.get("hiring_status", "likely"),
        **{k: v for k, v in kw.items() if k not in [
            "employee_count", "industry", "funding_stage",
            "estimated_annual_revenue", "tech_stack", "hiring_status",
        ]},
    }


def _make_apollo_company(name: str, domain: str, country: str = "United States") -> ApolloCompany:
    return ApolloCompany(
        id=f"id-{name}", name=name, domain=domain,
        country=country, employee_count=200,
    )


def _make_apollo_contact(email: str, company_id: str = "") -> ApolloContact:
    return ApolloContact(
        id=f"cid-{email}", email=email,
        first_name="Test", last_name="User",
        seniority="director", department="engineering",
        company_id=company_id,
    )


# ---------------------------------------------------------------------------
# Test 1: Geography filter runs BEFORE enrichment
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_geography_filter_before_enrichment(tmp_path: Path):
    """Companies outside allowed geography must be rejected BEFORE contact enrichment."""
    from core.skills.skill_4_find_leads import run_skill_4

    us_company = _make_apollo_company("Acme", "acme.com", "United States")
    sg_company = _make_apollo_company("SingaCorp", "singacorp.sg", "Singapore")

    search_response = ApolloSearchResponse(companies=[us_company, sg_company], total_count=2)

    contact_search_calls: list[str] = []

    async def mock_search_dm(company_domain: str, **kw):
        contact_search_calls.append(company_domain)
        return [_make_apollo_contact(f"test@{company_domain}", company_id=f"id-{company_domain}")]

    with (
        patch("core.skills.skill_4_find_leads.search_companies", new_callable=AsyncMock, return_value=search_response),
        patch("core.skills.skill_4_find_leads.search_decision_makers", side_effect=mock_search_dm),
        patch("core.skills.skill_4_find_leads.batch_enrich_organizations", new_callable=AsyncMock, return_value={}),
    ):
        result = await run_skill_4(
            offer_slug="test-offer",
            campaign_slug="test-campaign",
            offers_dir=str(tmp_path),
            apollo_api_key="fake-key",
        )

    # Singapore company must NOT have triggered contact enrichment
    assert "singacorp.sg" not in contact_search_calls, (
        "Geography filter must run before contact enrichment — Singapore company was enriched"
    )
    # US company should have been enriched
    assert "acme.com" in contact_search_calls


# ---------------------------------------------------------------------------
# Test 2: Two-stage pipeline (broad then strict)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_two_stage_pipeline(tmp_path: Path):
    """Two-stage pipeline: Stage 1 broad qualifies, enrichment runs, Stage 2 re-scores."""
    from core.skills.skill_4_find_leads import _two_stage_pipeline
    from services.icp.types import NormalizedIcpRules

    companies = [
        _make_company("GoodCo", "good.com", employee_count=300, industry="Technology"),
        _make_company("BadCo", "bad.com", employee_count=5, industry="Gambling"),
    ]

    # Broad rules: very low threshold, no hard filters
    broad_rules = NormalizedIcpRules(
        threshold=10.0,
        data_quality="accept-incomplete",
        max_critical_unknowns=10,
        hard_filters={},
        scoring={
            "hiring_signal": {"freshness_weight": 1.0, "intensity_weight": 1.0},
            "company_size": {},
            "funding": {"preferred": [], "acceptable": []},
            "revenue": {},
            "tech": {"preferred": [], "avoided": []},
            "industry": {"preferred": []},
            "domain": {"preferred": []},
            "intent": {},
        },
        enrichment={},
    )

    # Strict rules: higher threshold
    strict_rules = NormalizedIcpRules(
        threshold=100.0,
        data_quality="accept-incomplete",
        max_critical_unknowns=10,
        hard_filters={},
        scoring={
            "hiring_signal": {"freshness_weight": 1.0, "intensity_weight": 1.0},
            "company_size": {},
            "funding": {"preferred": [], "acceptable": []},
            "revenue": {},
            "tech": {"preferred": [], "avoided": []},
            "industry": {"preferred": []},
            "domain": {"preferred": []},
            "intent": {},
        },
        enrichment={},
    )

    with patch(
        "core.skills.skill_4_find_leads.batch_enrich_organizations",
        new_callable=AsyncMock,
        return_value={},
    ):
        result = await _two_stage_pipeline(
            companies=companies,
            search_rules=broad_rules,
            user_rules=strict_rules,
            apollo_api_key="fake",
            log=MagicMock(),
        )

    # Stage 1 broad should let things through, but strict stage 2 threshold (100)
    # will filter out companies that don't score high enough
    assert "qualified" in result
    assert "all_scored" in result
    # all_scored should contain all companies (stage1 rejected + enriched)
    assert len(result["all_scored"]) == len(companies)


# ---------------------------------------------------------------------------
# Test 3: CSV export produces file
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_csv_export(tmp_path: Path):
    """Skill 4 should write all_leads.csv and contacts.csv."""
    from core.skills.skill_4_find_leads import run_skill_4

    company = _make_apollo_company("ExportCo", "export.com", "United States")
    search_response = ApolloSearchResponse(companies=[company], total_count=1)
    contact = _make_apollo_contact("john@export.com", company_id="id-ExportCo")

    with (
        patch("core.skills.skill_4_find_leads.search_companies", new_callable=AsyncMock, return_value=search_response),
        patch("core.skills.skill_4_find_leads.search_decision_makers", new_callable=AsyncMock, return_value=[contact]),
        patch("core.skills.skill_4_find_leads.batch_enrich_organizations", new_callable=AsyncMock, return_value={}),
    ):
        result = await run_skill_4(
            offer_slug="test-offer",
            campaign_slug="test-campaign",
            offers_dir=str(tmp_path),
            apollo_api_key="fake-key",
        )

    leads_dir = tmp_path / "test-offer" / "campaigns" / "test-campaign" / "leads"
    assert (leads_dir / "all_leads.csv").exists(), "all_leads.csv must be created"
    assert (leads_dir / "contacts.csv").exists(), "contacts.csv must be created"
    assert (leads_dir / "run-summary.json").exists(), "run-summary.json must be created"
    assert result["contacts"] >= 0
