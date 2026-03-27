"""Apollo contact enrichment — find and enrich decision-makers."""

from __future__ import annotations

import httpx
import structlog

from clients.apollo.errors import handle_apollo_error
from clients.apollo.types import ApolloContact
from clients.apollo.utils import APOLLO_BASE_URL, api_headers

logger = structlog.get_logger()

CONTACT_TIMEOUT = 30.0


async def search_decision_makers(
    company_domain: str,
    api_key: str,
    seniorities: list[str] | None = None,
    departments: list[str] | None = None,
    max_contacts: int = 5,
) -> list[ApolloContact]:
    """Search for decision-makers at a company via Apollo people search.

    Args:
        company_domain: Company domain to search within.
        api_key: Apollo API key.
        seniorities: Filter by seniority levels.
        departments: Filter by departments.
        max_contacts: Maximum contacts to return.

    Returns:
        List of ApolloContact.
    """
    body = {
        "q_organization_domains": company_domain,
        "person_seniorities": seniorities or ["vp", "director", "head", "manager"],
        "person_departments": departments or ["engineering", "data"],
        "per_page": min(max_contacts, 25),
        "page": 1,
    }

    async with httpx.AsyncClient(timeout=CONTACT_TIMEOUT) as client:
        response = await client.post(
            f"{APOLLO_BASE_URL}/v1/mixed_people/search",
            headers=api_headers(api_key),
            json=body,
        )

        if response.status_code != 200:
            error = handle_apollo_error(response.status_code, response.text)
            if error.retryable:
                logger.warn("Apollo people search retryable error", domain=company_domain)
                return []
            raise error

        data = response.json()
        people = data.get("people") or []

        contacts = []
        for person in people[:max_contacts]:
            contact = _parse_apollo_contact(person)
            contacts.append(contact)

        return contacts


async def enrich_contact(email: str, api_key: str) -> ApolloContact | None:
    """Enrich a single contact by email."""
    body = {"email": email}

    async with httpx.AsyncClient(timeout=CONTACT_TIMEOUT) as client:
        response = await client.post(
            f"{APOLLO_BASE_URL}/v1/people/match",
            headers=api_headers(api_key),
            json=body,
        )

        if response.status_code != 200:
            logger.warn("Apollo contact enrich failed", email=email, status=response.status_code)
            return None

        data = response.json()
        person = data.get("person")
        if not person:
            return None

        return _parse_apollo_contact(person)


async def batch_enrich_contacts(
    emails: list[str],
    api_key: str,
    batch_size: int = 10,
) -> list[ApolloContact]:
    """Batch enrich contacts by email."""
    results: list[ApolloContact] = []

    for i in range(0, len(emails), batch_size):
        batch = emails[i : i + batch_size]
        body = {
            "details": [{"email": email} for email in batch],
        }

        async with httpx.AsyncClient(timeout=CONTACT_TIMEOUT) as client:
            response = await client.post(
                f"{APOLLO_BASE_URL}/v1/people/bulk_match",
                headers=api_headers(api_key),
                json=body,
            )

            if response.status_code != 200:
                logger.warn("Apollo bulk match failed", batch_size=len(batch))
                continue

            data = response.json()
            matches = data.get("matches") or []
            for match in matches:
                if match:
                    results.append(_parse_apollo_contact(match))

    return results


def _parse_apollo_contact(person: dict) -> ApolloContact:
    """Parse Apollo person response into our model."""
    org = person.get("organization") or {}

    return ApolloContact(
        id=person.get("id") or "",
        email=person.get("email") or "",
        first_name=person.get("first_name"),
        last_name=person.get("last_name"),
        name=person.get("name"),
        title=person.get("title"),
        seniority=person.get("seniority"),
        department=(person.get("departments") or [None])[0],
        phone=person.get("phone_number"),
        direct_email=person.get("personal_emails", [None])[0] if person.get("personal_emails") else None,
        email_status=person.get("email_status"),
        linkedin_url=person.get("linkedin_url"),
        linkedin_id=person.get("linkedin_id"),
        photos=person.get("photo_url", []) if isinstance(person.get("photo_url"), list) else [],
        company_id=org.get("id"),
    )
