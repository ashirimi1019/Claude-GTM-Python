"""Apollo.io API types."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ApolloCompany(BaseModel):
    """Company from Apollo search/enrichment."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = ""
    name: str = ""
    domain: str = ""
    website_url: str | None = None
    employee_count: int | None = None
    employee_range: str | None = None
    industry: str | None = None
    sub_industry: str | None = None
    sic_code: str | None = None
    funding_stage: str | None = None
    total_funding: float | None = None
    latest_funding_amount: float | None = None
    latest_funding_date: str | None = None
    estimated_annual_revenue: float | None = None
    estimated_annual_revenue_range: str | None = None
    tech_stack: list[str] | None = None
    keywords: list[str] | None = None
    countries: list[str] | None = None
    states: list[str] | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    linkedin_url: str | None = None
    company_status: str | None = None
    hiring_status: str | None = None
    raw_data: dict[str, Any] | None = None


class ApolloContact(BaseModel):
    """Contact from Apollo enrichment."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = ""
    email: str = ""
    first_name: str | None = None
    last_name: str | None = None
    name: str | None = None
    title: str | None = None
    seniority: str | None = None
    department: str | None = None
    phone: str | None = None
    direct_email: str | None = None
    email_status: str | None = None
    linkedin_url: str | None = None
    linkedin_id: str | None = None
    photos: list[str] | None = None
    company_id: str | None = None
    company: ApolloCompany | None = None


class ApolloQueryParams(BaseModel):
    """Parameters for Apollo company search."""

    employee_ranges: list[str] = []
    keywords: list[str] = []
    location_countries: list[str] = []
    location_states: list[str] = []
    per_page: int = 100
    page: int = 1


class ApolloSearchResponse(BaseModel):
    """Response from Apollo company search."""

    companies: list[ApolloCompany] = []
    total_count: int = 0
    errors: list[str] = []


class ApolloOrgEnrichmentResult(BaseModel):
    """Result from Apollo organization enrichment."""

    id: str = ""
    name: str = ""
    domain: str = ""
    industry: str | None = None
    keywords: list[str] | None = None
    employee_count: int | None = None
    funding_stage: str | None = None
    estimated_annual_revenue: float | None = None
    technology_names: list[str] | None = None
