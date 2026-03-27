"""Apollo organization enrichment — enrich companies with richer data."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import structlog

from clients.apollo.types import ApolloOrgEnrichmentResult
from clients.apollo.utils import APOLLO_BASE_URL, api_headers, normalize_domain

logger = structlog.get_logger()

ENRICH_TIMEOUT = 30.0


async def enrich_organization_by_domain(
    domain: str,
    api_key: str,
) -> ApolloOrgEnrichmentResult | None:
    """Enrich a single organization by domain via Apollo.

    Gracefully degrades on 404/403/402/422 — returns None.
    """
    normalized = normalize_domain(domain)

    async with httpx.AsyncClient(timeout=ENRICH_TIMEOUT) as client:
        response = await client.post(
            f"{APOLLO_BASE_URL}/v1/organizations/enrich",
            headers=api_headers(api_key),
            json={"domain": normalized},
        )

        if response.status_code in (404, 403, 402, 422):
            logger.info("Apollo org enrichment unavailable", domain=normalized, status=response.status_code)
            return None

        if response.status_code != 200:
            logger.warn("Apollo org enrichment failed", domain=normalized, status=response.status_code)
            return None

        data = response.json()
        org = data.get("organization")
        if not org:
            return None

        return ApolloOrgEnrichmentResult(
            id=org.get("id") or "",
            name=org.get("name") or "",
            domain=org.get("primary_domain") or normalized,
            industry=org.get("industry"),
            keywords=org.get("keywords"),
            employee_count=org.get("estimated_num_employees"),
            funding_stage=org.get("latest_funding_stage"),
            estimated_annual_revenue=org.get("annual_revenue"),
            technology_names=org.get("technology_names"),
        )


async def batch_enrich_organizations(
    domains: list[str],
    api_key: str,
    concurrency: int = 3,
) -> dict[str, ApolloOrgEnrichmentResult]:
    """Parallel-batch enrich organizations by domain.

    Returns:
        Dict mapping normalized domain → enrichment result.
    """
    # Deduplicate domains
    unique_domains = list({normalize_domain(d) for d in domains if d})

    results: dict[str, ApolloOrgEnrichmentResult] = {}
    semaphore = asyncio.Semaphore(concurrency)

    async def _enrich_one(domain: str) -> None:
        async with semaphore:
            result = await enrich_organization_by_domain(domain, api_key)
            if result:
                results[normalize_domain(domain)] = result

    tasks = [_enrich_one(d) for d in unique_domains]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning("Enrichment batch item failed", index=i, error=str(result))

    logger.info(
        "Batch enrichment complete",
        attempted=len(unique_domains),
        succeeded=len(results),
    )

    return results


def merge_enriched_data(
    sparse: dict[str, Any],
    enriched: ApolloOrgEnrichmentResult,
) -> dict[str, Any]:
    """Merge enriched data into sparse company data.

    Rules:
    - Fill null fields from enriched data
    - Append technology_names to keywords (case-insensitive dedup)
    - Preserve existing non-null values
    """
    merged = sparse.copy()

    # Fill missing scalar fields
    field_map = {
        "industry": enriched.industry,
        "employee_count": enriched.employee_count,
        "funding_stage": enriched.funding_stage,
        "estimated_annual_revenue": enriched.estimated_annual_revenue,
    }

    for field, value in field_map.items():
        if value is not None and (merged.get(field) is None or merged.get(field) == ""):
            merged[field] = value

    # Merge keywords + technology_names
    existing_keywords = set(
        k.lower() for k in (merged.get("keywords") or merged.get("tech_stack") or [])
    )
    new_tech = enriched.technology_names or []
    new_keywords = enriched.keywords or []

    combined = list(merged.get("keywords") or merged.get("tech_stack") or [])
    for keyword in new_tech + new_keywords:
        if keyword.lower() not in existing_keywords:
            combined.append(keyword)
            existing_keywords.add(keyword.lower())

    if combined:
        merged["tech_stack"] = combined
        merged["keywords"] = combined

    return merged
