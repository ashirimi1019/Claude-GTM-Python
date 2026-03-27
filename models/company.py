"""Company domain model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class Company(BaseModel):
    """A discovered company — maps to the `companies` table."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = ""
    apollo_id: str = ""
    name: str = ""
    domain: str = ""
    website_url: str | None = None
    employee_count: int | None = None
    employee_range: str | None = None
    founded_year: int | None = None
    industry: str | None = None
    sub_industry: str | None = None
    sic_code: str | None = None
    funding_stage: str | None = None
    total_funding: float | None = None
    latest_funding_amount: float | None = None
    latest_funding_date: datetime | None = None
    company_status: str | None = None
    linkedin_url: str | None = None
    facebook_url: str | None = None
    twitter_url: str | None = None
    crunchbase_url: str | None = None
    primary_industry: str | None = None
    primary_sub_industry: str | None = None
    estimated_annual_revenue: float | None = None
    estimated_annual_revenue_range: str | None = None
    tech_stack: list[str] | None = None
    countries: list[str] | None = None
    states: list[str] | None = None
    raw_address: str | None = None
    street_address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    hiring_status: str | None = None  # likely | unlikely | unknown
    hiring_signals: dict[str, Any] | None = None
    icp_score: float | None = None
    icp_tier: str | None = None  # A | B | C
    icp_confidence: float | None = None
    icp_stage: str | None = None
    icp_qualified: bool | None = None
    raw_data_json: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
