"""Skill 5 — Launch Outreach: read leads + copy, create sequences, enroll contacts.

Phases:
  a. Read CSV from Skill 4 + copy from Skill 3
  b. Group contacts by segment (decision_maker, influencer, implementer)
  c. Create/get Apollo sequences per segment (UNIQUE on campaign_id + segment_key)
  d. Add email steps to sequences from copy variants
  e. Enroll contacts via Apollo
  f. Write messages.csv to outreach/
  g. Persist to DB: messages, campaign_sequences
  h. Return counts
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import structlog

from clients.apollo.sequences import (
    activate_sequence,
    add_email_step,
    create_sequence,
    enroll_sequence,
    get_email_accounts,
)
from services.csv_export import export_messages_to_csv

logger = structlog.get_logger()


async def run_skill_5(
    offer_slug: str,
    campaign_slug: str,
    offers_dir: str = "offers",
    *,
    apollo_api_key: str = "",
    email_account_id: str | None = None,
    db_persist: Any | None = None,
    db_load_campaign: Any | None = None,
) -> dict[str, Any]:
    """Execute Skill 5: Launch Outreach.

    Returns {"sequences_created": int, "contacts_enrolled": int}.
    """
    log = logger.bind(skill=5, offer=offer_slug, campaign=campaign_slug)
    log.info("Skill 5 started")

    campaign_dir = Path(offers_dir) / offer_slug / "campaigns" / campaign_slug

    # ── a. Read CSV from Skill 4 + copy from Skill 3 ──
    contacts = _read_contacts_csv(campaign_dir / "leads" / "contacts.csv")
    if not contacts:
        # Fallback: try all_leads.csv
        contacts = _read_contacts_csv(campaign_dir / "leads" / "all_leads.csv")

    copy_variants = _read_copy_variants(campaign_dir / "copy" / "email-variants.md")
    log.info("Loaded inputs", contacts=len(contacts), copy_variants=len(copy_variants))

    if not contacts:
        log.warn("No contacts found — cannot launch outreach")
        return {"sequences_created": 0, "contacts_enrolled": 0}

    # ── b. Group contacts by segment ──
    segments = group_contacts_by_segment(contacts)
    log.info("Segments", segments={k: len(v) for k, v in segments.items()})

    # ── c. Resolve email account ──
    if not email_account_id and apollo_api_key:
        accounts = await get_email_accounts(apollo_api_key)
        if accounts:
            email_account_id = accounts[0].get("id", "")

    # ── d. Create sequences + add steps + enroll ──
    campaign_id = ""
    if db_load_campaign:
        campaign_data = await db_load_campaign(offer_slug, campaign_slug)
        campaign_id = str(campaign_data.get("id", "")) if campaign_data else ""

    sequences_created = 0
    total_enrolled = 0
    all_messages: list[dict[str, Any]] = []
    sequence_records: list[dict[str, Any]] = []

    for segment_key, segment_contacts in segments.items():
        if not segment_contacts:
            continue

        # Create sequence
        seq_name = f"{offer_slug}__{campaign_slug}__{segment_key}"
        seq = await create_sequence(seq_name, api_key=apollo_api_key)
        sequence_id = seq.get("id", "")
        sequences_created += 1

        sequence_records.append({
            "campaign_id": campaign_id,
            "segment_key": segment_key,
            "apollo_sequence_id": sequence_id,
            "sequence_name": seq_name,
        })

        # Add email steps from copy variants
        step_num = 1
        for variant in copy_variants:
            await add_email_step(
                sequence_id=sequence_id,
                subject=variant.get("subject", f"Step {step_num}"),
                body_template=variant.get("body", ""),
                api_key=apollo_api_key,
                wait_days=variant.get("wait_days", 3),
                step_number=step_num,
            )
            step_num += 1

        # Activate sequence
        await activate_sequence(sequence_id, api_key=apollo_api_key)

        # Enroll contacts
        contact_ids = [c.get("id", "") for c in segment_contacts if c.get("id")]
        if contact_ids and email_account_id:
            result = await enroll_sequence(
                sequence_id=sequence_id,
                contact_ids=contact_ids,
                email_account_id=email_account_id,
                api_key=apollo_api_key,
            )
            total_enrolled += result.get("enrolled", 0)

        # Build message records
        for contact in segment_contacts:
            all_messages.append({
                "contact_email": contact.get("email", ""),
                "company_name": contact.get("company_name", ""),
                "subject": copy_variants[0].get("subject", "") if copy_variants else "",
                "channel": "email",
                "status": "queued",
                "sent_at": None,
                "opened_at": None,
                "clicked_at": None,
                "replied_at": None,
            })

    # ── f. Write messages.csv ──
    outreach_dir = campaign_dir / "outreach"
    outreach_dir.mkdir(parents=True, exist_ok=True)
    export_messages_to_csv(all_messages, outreach_dir / "messages.csv")

    # ── g. Persist to DB ──
    if db_persist:
        await db_persist(
            campaign_id=campaign_id,
            messages=all_messages,
            sequences=sequence_records,
        )

    result = {
        "sequences_created": sequences_created,
        "contacts_enrolled": total_enrolled,
    }
    log.info("Skill 5 complete", **result)
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def group_contacts_by_segment(
    contacts: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group contacts by segment key.

    Valid segments: decision_maker, influencer, implementer, other.
    """
    groups: dict[str, list[dict[str, Any]]] = {
        "decision_maker": [],
        "influencer": [],
        "implementer": [],
        "other": [],
    }

    for contact in contacts:
        segment = contact.get("segment", "other")
        if segment not in groups:
            segment = "other"
        groups[segment].append(contact)

    # Remove empty groups
    return {k: v for k, v in groups.items() if v}


def _read_contacts_csv(filepath: Path) -> list[dict[str, Any]]:
    """Read contacts from a CSV file."""
    if not filepath.exists():
        return []

    contacts: list[dict[str, Any]] = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            contacts.append(dict(row))

    return contacts


def _read_copy_variants(filepath: Path) -> list[dict[str, str]]:
    """Parse email copy variants from a markdown file.

    Expected format: sections with ## Subject: ... and body text.
    """
    if not filepath.exists():
        return []

    text = filepath.read_text(encoding="utf-8")
    variants: list[dict[str, str]] = []

    # Split by ## headers
    sections = re.split(r"^##\s+", text, flags=re.MULTILINE)
    for section in sections:
        section = section.strip()
        if not section:
            continue

        lines = section.split("\n", 1)
        subject = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""

        # Clean "Subject: " prefix if present
        if subject.lower().startswith("subject:"):
            subject = subject[len("subject:"):].strip()

        if subject:
            variants.append({"subject": subject, "body": body, "wait_days": "3"})

    return variants
