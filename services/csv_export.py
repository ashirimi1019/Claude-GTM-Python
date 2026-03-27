"""CSV export services — companies, contacts, messages."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()

# Standard column definitions
COMPANY_COLUMNS = [
    "company_id", "apollo_id", "name", "domain", "employee_count",
    "industry", "funding_stage", "country", "icp_score", "icp_tier",
    "icp_confidence", "icp_stage", "icp_qualified",
]

CONTACT_COLUMNS = [
    "email", "first_name", "last_name", "title", "company_name",
    "company_domain", "seniority", "department", "email_status",
    "linkedin_url", "phone",
]

MESSAGE_COLUMNS = [
    "contact_email", "company_name", "subject", "channel", "status",
    "sent_at", "opened_at", "clicked_at", "replied_at",
]


def export_companies_to_csv(
    companies: list[dict[str, Any]],
    filepath: str | Path,
    extra_columns: list[str] | None = None,
) -> Path:
    """Export companies to CSV with standard columns.

    Args:
        companies: List of company dicts.
        filepath: Output CSV path.
        extra_columns: Additional columns to include (e.g., ICP two-stage fields).

    Returns:
        Path to the written file.
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    columns = COMPANY_COLUMNS + (extra_columns or [])

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for company in companies:
            row = {col: company.get(col, "") for col in columns}
            writer.writerow(row)

    logger.info("Exported companies CSV", filepath=str(filepath), count=len(companies))
    return filepath


def export_contacts_to_csv(
    contacts: list[dict[str, Any]],
    filepath: str | Path,
) -> Path:
    """Export contacts to CSV with standard columns."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CONTACT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for contact in contacts:
            row = {col: contact.get(col, "") for col in CONTACT_COLUMNS}
            writer.writerow(row)

    logger.info("Exported contacts CSV", filepath=str(filepath), count=len(contacts))
    return filepath


def export_messages_to_csv(
    messages: list[dict[str, Any]],
    filepath: str | Path,
) -> Path:
    """Export messages to CSV with standard columns."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MESSAGE_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for msg in messages:
            row = {col: msg.get(col, "") for col in MESSAGE_COLUMNS}
            writer.writerow(row)

    logger.info("Exported messages CSV", filepath=str(filepath), count=len(messages))
    return filepath
