"""Apollo company search — POST /v1/mixed_companies/search."""

from __future__ import annotations

import httpx
import structlog

from clients.apollo.types import ApolloCompany, ApolloQueryParams, ApolloSearchResponse
from clients.apollo.utils import APOLLO_BASE_URL, api_headers
from clients.apollo.errors import handle_apollo_error

logger = structlog.get_logger()

SEARCH_TIMEOUT = 30.0


async def search_companies(
    params: ApolloQueryParams,
    api_key: str,
    credit_budget: int = 100,
) -> ApolloSearchResponse:
    """Search for companies via Apollo mixed_companies/search.

    Args:
        params: Search parameters (employee ranges, keywords, locations).
        api_key: Apollo API key.
        credit_budget: Max pages to fetch (each page = ~1 credit).

    Returns:
        ApolloSearchResponse with companies and total count.
    """
    all_companies: list[ApolloCompany] = []
    total_count = 0
    page = params.page

    async with httpx.AsyncClient(timeout=SEARCH_TIMEOUT) as client:
        for _ in range(credit_budget):
            body = {
                "organization_num_employees_ranges": params.employee_ranges or [],
                "q_organization_keyword_tags": params.keywords[:10] if params.keywords else [],
                "organization_locations": params.location_countries or [],
                "per_page": min(params.per_page, 100),
                "page": page,
            }

            if params.location_states:
                body["person_locations"] = [
                    f"United States, {s}" for s in params.location_states
                ]

            logger.info("Apollo search", page=page, keywords=len(params.keywords or []))

            response = await client.post(
                f"{APOLLO_BASE_URL}/v1/mixed_companies/search",
                headers=api_headers(api_key),
                json=body,
            )

            if response.status_code != 200:
                error = handle_apollo_error(response.status_code, response.text)
                if error.retryable:
                    logger.warn("Apollo search retryable error", status=response.status_code)
                    break
                raise error

            data = response.json()
            organizations = data.get("organizations") or []

            if not organizations:
                break

            for org in organizations:
                company = _parse_apollo_company(org)
                all_companies.append(company)

            total_count = data.get("pagination", {}).get("total_entries", len(all_companies))

            # Check if there are more pages
            total_pages = data.get("pagination", {}).get("total_pages", 1)
            if page >= total_pages:
                break

            page += 1

    return ApolloSearchResponse(
        companies=all_companies,
        total_count=total_count,
    )


def _parse_apollo_company(org: dict) -> ApolloCompany:
    """Parse Apollo API organization response into our model."""
    return ApolloCompany(
        id=org.get("id") or "",
        name=org.get("name") or "",
        domain=org.get("primary_domain") or org.get("domain") or "",
        website_url=org.get("website_url"),
        employee_count=org.get("estimated_num_employees"),
        industry=org.get("industry"),
        sub_industry=org.get("sub_industry"),
        sic_code=str(org.get("sic_code") or ""),
        funding_stage=org.get("latest_funding_stage"),
        total_funding=org.get("total_funding"),
        latest_funding_amount=org.get("latest_funding_round_amount"),
        latest_funding_date=org.get("latest_funding_round_date"),
        estimated_annual_revenue=org.get("annual_revenue"),
        tech_stack=org.get("technology_names"),
        keywords=org.get("keywords"),
        country=org.get("country"),
        state=org.get("state"),
        city=org.get("city"),
        linkedin_url=org.get("linkedin_url"),
        raw_data=org,
    )
