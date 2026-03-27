"""Apollo sequence analytics — metrics retrieval."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from clients.apollo.errors import handle_apollo_error
from clients.apollo.utils import APOLLO_BASE_URL, api_headers

logger = structlog.get_logger()

ANALYTICS_TIMEOUT = 30.0


async def get_sequence_analytics(
    sequence_id: str,
    api_key: str,
) -> dict[str, Any]:
    """Get performance metrics for a sequence.

    Returns:
        Dict with sent, opened, clicked, replied, bounced, unsubscribed counts.
    """
    async with httpx.AsyncClient(timeout=ANALYTICS_TIMEOUT) as client:
        response = await client.get(
            f"{APOLLO_BASE_URL}/v1/emailer_campaigns/{sequence_id}",
            headers=api_headers(api_key),
        )

        if response.status_code != 200:
            raise handle_apollo_error(response.status_code, response.text)

        data = response.json()
        campaign = data.get("emailer_campaign") or {}

        return {
            "sequence_id": sequence_id,
            "name": campaign.get("name") or "",
            "active": campaign.get("active") or False,
            "sent": campaign.get("num_sent") or 0,
            "opened": campaign.get("unique_opened") or 0,
            "clicked": campaign.get("unique_clicked") or 0,
            "replied": campaign.get("unique_replied") or 0,
            "bounced": campaign.get("unique_bounced") or 0,
            "unsubscribed": campaign.get("unique_unsubscribed") or 0,
            "total_contacts": campaign.get("num_contacts") or 0,
        }


async def get_contact_activity_log(
    contact_id: str,
    api_key: str,
) -> list[dict[str, Any]]:
    """Get activity log for a specific contact."""
    async with httpx.AsyncClient(timeout=ANALYTICS_TIMEOUT) as client:
        response = await client.get(
            f"{APOLLO_BASE_URL}/v1/contacts/{contact_id}",
            headers=api_headers(api_key),
        )

        if response.status_code != 200:
            return []

        data = response.json()
        contact = data.get("contact") or {}
        return contact.get("activities") or []
