"""Deduplication services — contacts by email, companies by apollo_id/domain."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()


def deduplicate_contacts(contacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate contacts by email — keeps the record with most data.

    Args:
        contacts: List of contact dicts with 'email' field.

    Returns:
        Deduplicated list of contacts.
    """
    seen: dict[str, dict[str, Any]] = {}

    for contact in contacts:
        email = (contact.get("email") or "").lower().strip()
        if not email:
            continue

        if email in seen:
            # Merge: keep existing but fill in missing fields from duplicate
            existing = seen[email]
            for key, value in contact.items():
                if value is not None and (existing.get(key) is None or existing.get(key) == ""):
                    existing[key] = value
        else:
            seen[email] = contact.copy()

    deduped = list(seen.values())
    removed = len(contacts) - len(deduped)
    if removed > 0:
        logger.info("Deduplicated contacts", original=len(contacts), deduped=len(deduped), removed=removed)

    return deduped


def deduplicate_companies(companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate companies by apollo_id or domain — merges array fields.

    Args:
        companies: List of company dicts.

    Returns:
        Deduplicated list of companies.
    """
    seen_by_apollo_id: dict[str, dict[str, Any]] = {}
    seen_by_domain: dict[str, dict[str, Any]] = {}
    result: list[dict[str, Any]] = []

    for company in companies:
        apollo_id = company.get("apollo_id") or ""
        domain = (company.get("domain") or "").lower().strip()

        # Check for duplicates by apollo_id first, then domain
        existing = None
        if apollo_id and apollo_id in seen_by_apollo_id:
            existing = seen_by_apollo_id[apollo_id]
        elif domain and domain in seen_by_domain:
            existing = seen_by_domain[domain]

        if existing is not None:
            # Merge: fill missing fields, combine arrays
            for key, value in company.items():
                if value is not None and (existing.get(key) is None or existing.get(key) == ""):
                    existing[key] = value
                elif isinstance(value, list) and isinstance(existing.get(key), list):
                    # Combine arrays, deduplicate
                    combined = existing[key] + value
                    try:
                        combined = list(set(combined))
                    except TypeError:
                        # Contains unhashable types (dicts), use manual dedup
                        seen = []
                        for item in combined:
                            if item not in seen:
                                seen.append(item)
                        combined = seen
                    existing[key] = combined
        else:
            company_copy = company.copy()
            result.append(company_copy)
            if apollo_id:
                seen_by_apollo_id[apollo_id] = company_copy
            if domain:
                seen_by_domain[domain] = company_copy

    removed = len(companies) - len(result)
    if removed > 0:
        logger.info("Deduplicated companies", original=len(companies), deduped=len(result), removed=removed)

    return result


def deduplicate_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate messages by (campaign_id, contact_id, channel) — keeps latest."""
    seen: dict[str, dict[str, Any]] = {}

    for msg in messages:
        key = f"{msg.get('campaign_id')}:{msg.get('contact_id')}:{msg.get('channel')}"

        if key in seen:
            existing = seen[key]
            # Keep the one with the later sent_at
            existing_sent = existing.get("sent_at") or ""
            msg_sent = msg.get("sent_at") or ""
            if msg_sent > existing_sent:
                seen[key] = msg.copy()
        else:
            seen[key] = msg.copy()

    return list(seen.values())
