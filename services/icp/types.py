"""ICP pipeline types — profile, traces, rules, scoring results.

Convention: snake_case fields with camelCase aliases for DB JSONB compatibility.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# --- Strictness ---

class StrictnessConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    level: Literal["broad", "balanced", "strict", "very_strict"] = "broad"
    expert_overrides: dict[str, Any] | None = Field(None, alias="expertOverrides")


# --- Hard Filters ---

class CompanySizeFilter(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    hard_min: int | None = Field(None, alias="hardMin")
    hard_max: int | None = Field(None, alias="hardMax")
    reject_outside: bool = Field(False, alias="rejectOutside")
    preset: str | None = None


class TechMustHave(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    keywords: list[str] = []
    behavior: Literal["require-when-data-exists", "require-always"] = "require-when-data-exists"


class GeographyFilter(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    allowed_countries: list[str] = Field(default_factory=list, alias="allowedCountries")
    allowed_us_states: list[str] | None = Field(None, alias="allowedUsStates")


class HardFiltersConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    company_size: CompanySizeFilter | None = Field(None, alias="company_size")
    industry_excluded: list[str] | None = Field(None, alias="industry_excluded")
    industry_required: list[str] | None = Field(None, alias="industry_required")
    funding_excluded: list[str] | None = Field(None, alias="funding_excluded")
    funding_required: list[str] | None = Field(None, alias="funding_required")
    competitor: bool | None = None
    tech_must_have: TechMustHave | None = Field(None, alias="tech_must_have")
    hiring_required: bool | None = Field(None, alias="hiring_required")
    intent_required: bool | None = Field(None, alias="intent_required")
    geography: GeographyFilter | None = None


# --- Scoring ---

class HiringSignalWeights(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    freshness_weight: float = Field(1.0, alias="freshnessWeight")
    intensity_weight: float = Field(1.0, alias="intensityWeight")


class CompanySizeBands(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ideal: list[int] = []  # [min, max]
    acceptable: list[int] = []
    partial: list[int] = []


class TechStackScoring(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    preferred: list[str] = []
    nice_to_have: list[str] = Field(default_factory=list, alias="niceToHave")
    avoided: list[str] = []
    weights: dict[str, float] | None = None


class IntentScoring(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    min_score: float = Field(0.0, alias="minScore")
    topics: list[str] = []


class ScoringConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    hiring_signal: dict[str, Any] | None = Field(None, alias="hiringSignal")
    company_size: dict[str, Any] | None = Field(None, alias="companySize")
    funding: dict[str, Any] | None = None
    revenue: dict[str, Any] | None = None
    tech_stack: TechStackScoring | None = Field(None, alias="techStack")
    industry: dict[str, Any] | None = None
    domain: dict[str, Any] | None = None
    intent: IntentScoring | None = None


# --- Enrichment ---

class EnrichmentConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    seniorities: list[str] = []
    departments: list[str] = []
    max_contacts_per_company: int = Field(3, alias="maxContactsPerCompany")
    require_verified_email: bool = Field(True, alias="requireVerifiedEmail")


# --- ICP Profile (v1) ---

class IcpProfile(BaseModel):
    """The ICP Profile — ABSOLUTE source of truth when not null in DB."""

    model_config = ConfigDict(populate_by_name=True)

    version: int = 1
    mode: Literal["basic", "advanced"] = "basic"
    strictness: StrictnessConfig = Field(default_factory=StrictnessConfig)
    hard_filters: HardFiltersConfig | None = Field(None, alias="hardFilters")
    scoring: ScoringConfig | None = None
    enrichment: EnrichmentConfig | None = None


# --- Execution Traces ---

IcpOutcome = Literal[
    "qualified",
    "rejected-hard-filter",
    "rejected-confidence",
    "rejected-scoring",
    "rejected-after-enrichment",
]


class IcpFilterTrace(BaseModel):
    """Result of a single hard-filter gate."""
    gate: str = ""
    passed: bool = True
    reason: str = ""
    rule_value: Any = None
    company_value: Any = None


class IcpScoringTrace(BaseModel):
    """Breakdown of scoring across 8 dimensions."""
    dimensions: dict[str, float] = {}
    total: float = 0.0
    max_possible: float = 0.0
    threshold: float = 0.0
    zero_dimensions: list[str] = []
    missing_points: float = 0.0


class IcpConfidenceScore(BaseModel):
    """Data quality confidence assessment."""
    overall: float = 0.0
    meets_requirement: bool = False
    critical_unknowns: int = 0
    data_completeness: float = 0.0
    match_strength: float = 0.0


class IcpCompanyTrace(BaseModel):
    """Full trace for one company through the ICP pipeline."""
    company_id: str = ""
    apollo_id: str | None = None
    company_name: str = ""
    outcome: IcpOutcome = "rejected-scoring"
    hard_filters: list[IcpFilterTrace] = []
    scoring: IcpScoringTrace | None = None
    confidence: IcpConfidenceScore | None = None
    tier: Literal["A", "B", "C"] | None = None


class IcpTwoStageTrace(BaseModel):
    """Two-stage pipeline trace (Stage 1 broad + Stage 2 user strictness)."""
    stage1: IcpCompanyTrace | None = None
    stage2: IcpCompanyTrace | None = None
    enrichment_attempted: bool = False
    enrichment_succeeded: bool = False
    enrichment_error: str | None = None
    final_outcome: IcpOutcome = "rejected-scoring"
    final_tier: Literal["A", "B", "C"] | None = None


# --- Normalized Rules (output of normalizer, input to executor) ---

class NormalizedIcpRules(BaseModel):
    """Fully resolved rules ready for execution."""
    model_config = ConfigDict(populate_by_name=True)

    threshold: float = 75.0
    data_quality: str = "accept-incomplete"
    max_critical_unknowns: int = 3
    hard_filters: dict[str, Any] = {}
    scoring: dict[str, Any] = {}
    enrichment: dict[str, Any] = {}
    enforcement: dict[str, Any] = {}
