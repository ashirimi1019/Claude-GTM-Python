"""Contact domain model."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Contact(BaseModel):
    """A decision-maker contact — maps to the `contacts` table. Email is UNIQUE."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = ""
    apollo_contact_id: str | None = None
    email: str  # REQUIRED — UNIQUE constraint in DB
    first_name: str = ""
    last_name: str = ""
    title: str | None = None
    company_id: str | None = None
    seniority: str | None = None  # vp | director | head | manager | individual_contributor | other
    department: str | None = None  # engineering | data | product | sales | other
    phone: str | None = None
    linkedin_url: str | None = None
    direct_email: str | None = None
    email_status: str = "unverified"  # verified | unverified | bounced | opted_out
    prospect_status: str | None = None
    prospect_stage: str | None = None
    prospect_person_titles: list[str] | None = None
    person_email_domain: str | None = None
    person_phone_numbers: list[dict[str, str]] | None = None
    person_photos: list[str] | None = None
    linkedin_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
