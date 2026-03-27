"""Campaign domain model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from models.offer import slugify


class Campaign(BaseModel):
    """A campaign definition — maps to the `campaigns` table."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = ""
    offer_id: str = ""
    slug: str = ""
    title: str = ""
    vertical_id: str | None = None
    status: str = "draft"  # draft | active | paused | completed | archived
    allowed_countries: list[str] | None = None
    allowed_us_states: list[str] | None = None
    icp_profile: dict[str, Any] | None = None
    scoring_config_overrides: dict[str, Any] | None = None
    lead_count: int = 0
    qualified_count: int = 0
    message_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str = ""


class CampaignCreate(BaseModel):
    """Input schema for creating a new campaign."""

    offer_slug: str
    name: str
    vertical_id: str | None = None
    allowed_countries: list[str] | None = None
    allowed_us_states: list[str] | None = None
    slug: str = ""

    @model_validator(mode="after")
    def _generate_slug(self) -> CampaignCreate:
        if not self.slug:
            self.slug = slugify(self.name)
        return self
