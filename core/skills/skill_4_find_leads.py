"""Skill 4 — Find Leads: company search, ICP pipeline, contact enrichment, CSV export.

This is the most complex skill. Two-stage ICP pipeline:
  Stage 1: broad search (high recall) against sparse Apollo data
  Enrichment: batch enrich shortlisted companies
  Stage 2: user-strictness scoring on enriched data
Then contact enrichment, deduplication, segmentation, CSV export, DB persistence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

from clients.apollo.contacts import search_decision_makers
from clients.apollo.enrichment import batch_enrich_organizations, merge_enriched_data
from clients.apollo.search import search_companies
from clients.apollo.types import ApolloQueryParams
from services.csv_export import export_companies_to_csv, export_contacts_to_csv
from services.deduplication import deduplicate_companies, deduplicate_contacts
from services.geography import filter_companies_by_geography, resolve_geography
from services.icp.apollo_query import build_apollo_query
from services.icp.executor import execute_icp_pipeline
from services.icp.normalizer import normalize_for_search_stage
from services.icp.resolver import resolve_execution_config
from services.icp.types import IcpProfile
from services.intelligence import assign_contact_segment

logger = structlog.get_logger()

# Two-stage CSV columns appended to standard company columns
TWO_STAGE_EXTRA_COLUMNS = [
    "stage1_score",
    "stage1_tier",
    "stage1_outcome",
    "stage2_score",
    "stage2_tier",
    "stage2_outcome",
    "enrichment_succeeded",
]


async def run_skill_4(
    offer_slug: str,
    campaign_slug: str,
    offers_dir: str = "offers",
    *,
    # Dependency-injection hooks for testability
    db_load_offer: Any | None = None,
    db_load_campaign: Any | None = None,
    apollo_api_key: str = "",
    db_persist: Any | None = None,
) -> dict[str, Any]:
    """Execute Skill 4: Find Leads.

    Returns {"companies": int, "contacts": int, "qualified": int, "credits_estimate": int}.
    """
    log = logger.bind(skill=4, offer=offer_slug, campaign=campaign_slug)
    log.info("Skill 4 started")

    # ── a. Load offer + campaign ──
    offer = await _load_offer(offer_slug, offers_dir, db_load_offer)
    campaign = await _load_campaign(offer_slug, campaign_slug, offers_dir, db_load_campaign)

    # ── b. Resolve ICP config ──
    exec_config = resolve_execution_config(campaign, offer)
    mode = exec_config["mode"]
    log.info("ICP mode resolved", mode=mode)

    # ── c. Build Apollo search query ──
    if mode == "icp_builder" and exec_config.get("rules"):
        rules = exec_config["rules"]
        search_rules = _build_search_stage_rules(exec_config)
        apollo_params_dict = build_apollo_query(search_rules)
    else:
        # Legacy mode — use basic params
        apollo_params_dict = _build_legacy_apollo_params(campaign, offer)
        rules = None
        search_rules = None

    apollo_params = _dict_to_query_params(apollo_params_dict)

    # ── d. Search companies via Apollo ──
    search_result = await search_companies(apollo_params, api_key=apollo_api_key)
    raw_companies = [c.model_dump() for c in search_result.companies]
    log.info("Apollo search returned", count=len(raw_companies), total=search_result.total_count)

    # ── e. Geography filter (BEFORE enrichment — saves credits) ──
    allowed_countries, allowed_states = resolve_geography(
        offer_countries=offer.get("allowed_countries"),
        campaign_countries=campaign.get("allowed_countries"),
        offer_states=offer.get("allowed_us_states"),
        campaign_states=campaign.get("allowed_us_states"),
    )
    geo_filtered = filter_companies_by_geography(raw_companies, allowed_countries, allowed_states)
    log.info("Geography filter", before=len(raw_companies), after=len(geo_filtered))

    # Deduplicate companies
    geo_filtered = deduplicate_companies(geo_filtered)

    # ── f. Two-stage ICP pipeline ──
    if mode == "icp_builder" and search_rules is not None and rules is not None:
        result = await _two_stage_pipeline(
            companies=geo_filtered,
            search_rules=search_rules,
            user_rules=rules,
            apollo_api_key=apollo_api_key,
            log=log,
        )
        qualified_companies = result["qualified"]
        all_scored = result["all_scored"]
    else:
        # Legacy path — all geo-filtered companies are "qualified"
        qualified_companies = geo_filtered
        all_scored = geo_filtered

    log.info("ICP pipeline complete", qualified=len(qualified_companies))

    # ── g. Contact enrichment (only qualified companies) ──
    all_contacts: list[dict[str, Any]] = []
    enrichment_cfg = (rules.enrichment if rules else {}) or {}
    max_contacts = enrichment_cfg.get("max_contacts_per_company", 3)
    seniorities = enrichment_cfg.get("seniorities") or None
    departments = enrichment_cfg.get("departments") or None

    for company in qualified_companies:
        domain = company.get("domain", "")
        if not domain:
            continue
        contacts = await search_decision_makers(
            company_domain=domain,
            api_key=apollo_api_key,
            seniorities=seniorities,
            departments=departments,
            max_contacts=max_contacts,
        )
        for c in contacts:
            contact_dict = c.model_dump() if hasattr(c, "model_dump") else dict(c)
            contact_dict["company_name"] = company.get("name", "")
            contact_dict["company_domain"] = domain
            all_contacts.append(contact_dict)

    # ── h. Deduplicate contacts ──
    deduped_contacts = deduplicate_contacts(all_contacts)
    log.info("Contacts", raw=len(all_contacts), deduped=len(deduped_contacts))

    # ── i. Classification — assign segments ──
    for contact in deduped_contacts:
        company_for_contact = _find_company_for_contact(contact, qualified_companies)
        segment_info = assign_contact_segment(contact, company_for_contact)
        contact.update(segment_info)

    # ── j. CSV export ──
    campaign_dir = Path(offers_dir) / offer_slug / "campaigns" / campaign_slug
    leads_dir = campaign_dir / "leads"
    leads_dir.mkdir(parents=True, exist_ok=True)

    export_companies_to_csv(
        all_scored,
        leads_dir / "all_leads.csv",
        extra_columns=TWO_STAGE_EXTRA_COLUMNS,
    )
    export_contacts_to_csv(deduped_contacts, leads_dir / "contacts.csv")

    # ── k. Persist to DB ──
    if db_persist:
        await db_persist(
            offer_slug=offer_slug,
            campaign_slug=campaign_slug,
            companies=qualified_companies,
            contacts=deduped_contacts,
        )

    # ── l. Write run-summary.json ──
    credits_estimate = len(raw_companies) + len(qualified_companies) * 2
    summary = {
        "companies_searched": len(raw_companies),
        "geo_filtered": len(geo_filtered),
        "qualified": len(qualified_companies),
        "contacts": len(deduped_contacts),
        "credits_estimate": credits_estimate,
        "mode": mode,
    }
    summary_path = campaign_dir / "leads" / "run-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    # ── m. Return result ──
    result_dict = {
        "companies": len(all_scored),
        "contacts": len(deduped_contacts),
        "qualified": len(qualified_companies),
        "credits_estimate": credits_estimate,
    }
    log.info("Skill 4 complete", **result_dict)
    return result_dict


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _load_offer(
    offer_slug: str, offers_dir: str, db_loader: Any | None
) -> dict[str, Any]:
    """Load offer from DB or filesystem fallback."""
    if db_loader:
        offer = await db_loader(offer_slug)
        if offer:
            return offer

    # Filesystem fallback — read positioning.md for minimal data
    pos_path = Path(offers_dir) / offer_slug / "positioning.md"
    if pos_path.exists():
        return {"slug": offer_slug, "positioning_path": str(pos_path)}

    return {"slug": offer_slug}


async def _load_campaign(
    offer_slug: str, campaign_slug: str, offers_dir: str, db_loader: Any | None
) -> dict[str, Any]:
    """Load campaign from DB or filesystem fallback."""
    if db_loader:
        campaign = await db_loader(offer_slug, campaign_slug)
        if campaign:
            return campaign

    strategy_path = Path(offers_dir) / offer_slug / "campaigns" / campaign_slug / "strategy.md"
    if strategy_path.exists():
        return {"slug": campaign_slug, "strategy_path": str(strategy_path)}

    return {"slug": campaign_slug}


def _build_search_stage_rules(exec_config: dict[str, Any]):
    """Build Stage 1 (broad) rules from the ICP Builder profile."""
    profile_data = exec_config.get("profile")
    if profile_data:
        profile = IcpProfile.model_validate(profile_data)
        return normalize_for_search_stage(profile)
    return exec_config.get("rules")


def _build_legacy_apollo_params(
    campaign: dict[str, Any], offer: dict[str, Any]
) -> dict[str, Any]:
    """Build basic Apollo params for legacy mode."""
    return {
        "organization_locations": campaign.get("allowed_countries") or offer.get("allowed_countries") or [],
    }


def _dict_to_query_params(params: dict[str, Any]) -> ApolloQueryParams:
    """Convert raw dict from build_apollo_query into ApolloQueryParams."""
    keywords_raw = params.get("q_keywords", "")
    keywords = keywords_raw.split() if isinstance(keywords_raw, str) else list(keywords_raw)
    return ApolloQueryParams(
        employee_ranges=params.get("organization_num_employees_ranges", []),
        keywords=keywords,
        location_countries=params.get("organization_locations", []),
        location_states=params.get("person_locations", []),
    )


async def _two_stage_pipeline(
    companies: list[dict[str, Any]],
    search_rules,
    user_rules,
    apollo_api_key: str,
    log: Any,
) -> dict[str, Any]:
    """Run two-stage ICP pipeline: broad search → enrich → strict scoring."""
    # Stage 1: broad scoring (high recall)
    stage1 = execute_icp_pipeline(search_rules, companies)
    stage1_qualified = stage1["qualified"]
    stage1_rejected = stage1["rejected"]
    log.info("Stage 1 complete", qualified=len(stage1_qualified), rejected=len(stage1_rejected))

    # Tag stage 1 results on companies
    _tag_stage_results(stage1, stage_prefix="stage1")

    # Enrichment: batch enrich shortlisted companies
    domains = [c.get("domain", "") for c in stage1_qualified if c.get("domain")]
    enriched_map = await batch_enrich_organizations(domains, api_key=apollo_api_key)

    enriched_companies = []
    for company in stage1_qualified:
        domain = company.get("domain", "").lower().strip()
        enrichment = enriched_map.get(domain)
        if enrichment:
            company = merge_enriched_data(company, enrichment)
            company["enrichment_succeeded"] = True
        else:
            company["enrichment_succeeded"] = False
        enriched_companies.append(company)

    # Stage 2: user-strictness scoring on enriched data
    stage2 = execute_icp_pipeline(user_rules, enriched_companies)
    stage2_qualified = stage2["qualified"]
    log.info("Stage 2 complete", qualified=len(stage2_qualified), rejected=len(stage2["rejected"]))

    # Tag stage 2 results
    _tag_stage_results(stage2, stage_prefix="stage2")

    # Build all_scored: stage1_rejected get stage1 tags only; enriched get both
    all_scored = list(stage1_rejected) + enriched_companies

    return {
        "qualified": stage2_qualified,
        "all_scored": all_scored,
    }


def _tag_stage_results(pipeline_result: dict[str, Any], stage_prefix: str) -> None:
    """Tag companies with stage score/tier/outcome from pipeline traces."""
    traces = pipeline_result.get("traces", [])
    # Build lookup by company_id or company_name
    trace_lookup: dict[str, Any] = {}
    for trace in traces:
        key = trace.company_id or trace.company_name
        trace_lookup[key] = trace

    for company in pipeline_result["qualified"] + pipeline_result["rejected"]:
        key = str(company.get("id", "")) or company.get("name", "")
        trace = trace_lookup.get(key)
        if trace:
            company[f"{stage_prefix}_score"] = trace.scoring.total if trace.scoring else 0
            company[f"{stage_prefix}_tier"] = trace.tier
            company[f"{stage_prefix}_outcome"] = trace.outcome
        else:
            company[f"{stage_prefix}_outcome"] = "no-trace"


def _find_company_for_contact(
    contact: dict[str, Any], companies: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Find the matching company for a contact by domain."""
    domain = (contact.get("company_domain") or "").lower().strip()
    if not domain:
        return None
    for company in companies:
        if (company.get("domain") or "").lower().strip() == domain:
            return company
    return None
