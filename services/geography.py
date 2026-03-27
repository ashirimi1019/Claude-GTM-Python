"""Geography filtering — single source of truth for all country/state logic.

Default scope: Americas. All other geography logic must use this module.
"""

from __future__ import annotations

import structlog
from typing import Any

logger = structlog.get_logger()

# Default allowed countries — Americas scope
DEFAULT_ALLOWED_COUNTRIES: list[str] = [
    "United States",
    "Canada",
    "Mexico",
    "Brazil",
    "Argentina",
    "Chile",
    "Colombia",
    "Peru",
    "Uruguay",
]


def resolve_geography(
    offer_countries: list[str] | None = None,
    campaign_countries: list[str] | None = None,
    offer_states: list[str] | None = None,
    campaign_states: list[str] | None = None,
) -> tuple[list[str], list[str] | None]:
    """Resolve effective geography — campaign overrides offer, offer overrides default.

    Returns:
        (allowed_countries, allowed_us_states)
    """
    countries = campaign_countries or offer_countries or DEFAULT_ALLOWED_COUNTRIES
    states = campaign_states if campaign_states is not None else offer_states
    return countries, states


def check_company_geography(
    company: dict[str, Any],
    allowed_countries: list[str],
    allowed_states: list[str] | None = None,
) -> bool:
    """Check if a company's location is within allowed geography.

    Args:
        company: Dict with 'country', 'state', 'countries', 'states' fields.
        allowed_countries: List of allowed country names.
        allowed_states: Optional list of allowed US state codes.

    Returns:
        True if the company passes the geography filter.
    """
    # Check primary country
    country = company.get("country") or ""
    countries = company.get("countries") or []

    # Normalize for comparison
    allowed_lower = {c.lower().strip() for c in allowed_countries}

    # Check if any of the company's countries match
    company_countries = [country] + (countries if isinstance(countries, list) else [])
    country_match = any(
        c.lower().strip() in allowed_lower
        for c in company_countries
        if c
    )

    if not country_match:
        return False

    # If US states are specified, check state too
    if allowed_states is not None and country.lower().strip() == "united states":
        state = company.get("state") or ""
        states = company.get("states") or []
        allowed_states_lower = {s.lower().strip() for s in allowed_states}

        company_states = [state] + (states if isinstance(states, list) else [])
        state_match = any(
            s.lower().strip() in allowed_states_lower
            for s in company_states
            if s
        )
        if not state_match:
            return False

    return True


def filter_companies_by_geography(
    companies: list[dict[str, Any]],
    allowed_countries: list[str],
    allowed_states: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Filter companies by geography, logging rejections.

    Runs BEFORE contact enrichment to save Apollo credits.
    """
    passed: list[dict[str, Any]] = []
    rejected = 0

    for company in companies:
        if check_company_geography(company, allowed_countries, allowed_states):
            passed.append(company)
        else:
            rejected += 1
            logger.info(
                "[GEOGRAPHY REJECT]",
                company=company.get("name", "unknown"),
                country=company.get("country", "unknown"),
            )

    if rejected > 0:
        logger.info(
            "Geography filtering complete",
            passed=len(passed),
            rejected=rejected,
            total=len(companies),
        )

    return passed


def build_apollo_location_filter(
    countries: list[str],
    states: list[str] | None = None,
) -> dict[str, list[str]]:
    """Build Apollo API location filter params."""
    result: dict[str, list[str]] = {"organization_locations": countries}
    if states:
        result["person_locations"] = [f"United States, {s}" for s in states]
    return result
