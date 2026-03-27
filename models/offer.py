"""Offer domain model."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


def slugify(name: str) -> str:
    """Convert a name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


class Offer(BaseModel):
    """An offer definition with positioning — maps to the `offers` table."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_name=True)

    id: str = ""
    slug: str = ""
    name: str = Field("", alias="title")
    description: str = ""
    default_vertical_id: str | None = None
    status: str = "draft"  # draft | active | paused | archived
    allowed_countries: list[str] | None = None
    allowed_us_states: list[str] | None = None
    scoring_config_overrides: dict[str, Any] | None = None
    icp_profile: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str = ""


class OfferCreate(BaseModel):
    """Input schema for creating a new offer."""

    name: str
    description: str = ""
    vertical_id: str | None = None
    allowed_countries: list[str] | None = None
    allowed_us_states: list[str] | None = None
    slug: str = ""

    @model_validator(mode="after")
    def _generate_slug(self) -> OfferCreate:
        if not self.slug:
            self.slug = slugify(self.name)
        return self
