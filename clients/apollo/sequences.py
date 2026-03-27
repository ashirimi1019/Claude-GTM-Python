"""Apollo sequence management — create, enroll, pause, remove."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from clients.apollo.utils import APOLLO_BASE_URL, api_headers
from clients.apollo.errors import handle_apollo_error

logger = structlog.get_logger()

SEQUENCE_TIMEOUT = 30.0


async def create_sequence(
    name: str,
    api_key: str,
    permissions: str = "team_can_use",
) -> dict[str, Any]:
    """Create a new Apollo emailer campaign (sequence)."""
    body = {
        "name": name,
        "permissions": permissions,
        "active": False,  # Activate after adding steps
    }

    async with httpx.AsyncClient(timeout=SEQUENCE_TIMEOUT) as client:
        response = await client.post(
            f"{APOLLO_BASE_URL}/v1/emailer_campaigns",
            headers=api_headers(api_key),
            json=body,
        )

        if response.status_code not in (200, 201):
            raise handle_apollo_error(response.status_code, response.text)

        data = response.json()
        campaign = data.get("emailer_campaign") or {}
        return {"id": campaign.get("id"), "name": campaign.get("name")}


async def add_email_step(
    sequence_id: str,
    subject: str,
    body_template: str,
    api_key: str,
    wait_days: int = 3,
    step_number: int = 1,
) -> dict[str, Any]:
    """Add an email step to a sequence."""
    body = {
        "emailer_campaign_id": sequence_id,
        "emailer_step": {
            "type": "auto_email",
            "wait_time": wait_days,
            "position": step_number,
            "subject": subject,
            "body_template": body_template,
        },
    }

    async with httpx.AsyncClient(timeout=SEQUENCE_TIMEOUT) as client:
        response = await client.post(
            f"{APOLLO_BASE_URL}/v1/emailer_steps",
            headers=api_headers(api_key),
            json=body,
        )

        if response.status_code not in (200, 201):
            raise handle_apollo_error(response.status_code, response.text)

        return response.json()


async def activate_sequence(sequence_id: str, api_key: str) -> None:
    """Activate a sequence to start sending."""
    body = {"emailer_campaign": {"active": True}}

    async with httpx.AsyncClient(timeout=SEQUENCE_TIMEOUT) as client:
        response = await client.put(
            f"{APOLLO_BASE_URL}/v1/emailer_campaigns/{sequence_id}",
            headers=api_headers(api_key),
            json=body,
        )

        if response.status_code != 200:
            raise handle_apollo_error(response.status_code, response.text)


async def enroll_sequence(
    sequence_id: str,
    contact_ids: list[str],
    email_account_id: str,
    api_key: str,
) -> dict[str, int]:
    """Enroll contacts into a sequence.

    Returns:
        Dict with 'enrolled' and 'failed' counts.
    """
    body = {
        "contact_ids": contact_ids,
        "emailer_campaign_id": sequence_id,
        "send_email_from_email_account_id": email_account_id,
    }

    async with httpx.AsyncClient(timeout=SEQUENCE_TIMEOUT) as client:
        response = await client.post(
            f"{APOLLO_BASE_URL}/v1/emailer_campaigns/{sequence_id}/add_contact_ids",
            headers=api_headers(api_key),
            json=body,
        )

        if response.status_code != 200:
            raise handle_apollo_error(response.status_code, response.text)

        data = response.json()
        contacts = data.get("contacts") or []
        return {"enrolled": len(contacts), "failed": len(contact_ids) - len(contacts)}


async def pause_sequence(sequence_id: str, api_key: str) -> None:
    """Pause a sequence — safety action for high bounce rates."""
    body = {"emailer_campaign": {"active": False}}

    async with httpx.AsyncClient(timeout=SEQUENCE_TIMEOUT) as client:
        response = await client.put(
            f"{APOLLO_BASE_URL}/v1/emailer_campaigns/{sequence_id}",
            headers=api_headers(api_key),
            json=body,
        )

        if response.status_code != 200:
            logger.error("Failed to pause sequence", sequence_id=sequence_id)
            raise handle_apollo_error(response.status_code, response.text)

        logger.info("Sequence paused", sequence_id=sequence_id)


async def remove_contacts_from_sequence(
    sequence_id: str,
    contact_ids: list[str],
    api_key: str,
) -> None:
    """Remove contacts from a sequence — safety action."""
    body = {"contact_ids": contact_ids}

    async with httpx.AsyncClient(timeout=SEQUENCE_TIMEOUT) as client:
        response = await client.post(
            f"{APOLLO_BASE_URL}/v1/emailer_campaigns/{sequence_id}/remove_or_stop_contact_ids",
            headers=api_headers(api_key),
            json=body,
        )

        if response.status_code != 200:
            logger.error("Failed to remove contacts", sequence_id=sequence_id, count=len(contact_ids))
            raise handle_apollo_error(response.status_code, response.text)

        logger.info("Contacts removed from sequence", sequence_id=sequence_id, count=len(contact_ids))


async def get_email_accounts(api_key: str) -> list[dict[str, Any]]:
    """List available email accounts for sending."""
    async with httpx.AsyncClient(timeout=SEQUENCE_TIMEOUT) as client:
        response = await client.get(
            f"{APOLLO_BASE_URL}/v1/email_accounts",
            headers=api_headers(api_key),
        )

        if response.status_code != 200:
            raise handle_apollo_error(response.status_code, response.text)

        data = response.json()
        return data.get("email_accounts") or []
