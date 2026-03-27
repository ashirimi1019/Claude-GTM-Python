"""ICP pipeline constants — strictness bundles, size presets, scoring max, competitor keywords."""

# Maximum achievable ICP score across all 8 dimensions
MAX_SCORE = 215

# Per-dimension max scores
DIMENSION_MAX = {
    "hiring_signal": 40,
    "company_size": 50,
    "funding": 30,
    "revenue": 20,
    "tech_stack": 45,
    "industry": 15,
    "domain": 15,
    "intent": 35,
}

# Strictness bundles — predefined threshold + enforcement rules
STRICTNESS_BUNDLES: dict[str, dict] = {
    "broad": {
        "threshold": 75,
        "require_preferred_funding": False,
        "require_preferred_industries": False,
        "reject_missing_tech": False,
        "reject_missing_revenue": False,
        "data_quality": "accept-incomplete",
        "max_critical_unknowns": 3,
    },
    "balanced": {
        "threshold": 115,
        "require_preferred_funding": False,
        "require_preferred_industries": False,
        "reject_missing_tech": False,
        "reject_missing_revenue": False,
        "data_quality": "prefer-complete",
        "max_critical_unknowns": 2,
    },
    "strict": {
        "threshold": 165,
        "require_preferred_funding": True,
        "require_preferred_industries": True,
        "reject_missing_tech": True,
        "reject_missing_revenue": True,
        "data_quality": "prefer-complete",
        "max_critical_unknowns": 1,
    },
    "very_strict": {
        "threshold": 195,
        "require_preferred_funding": True,
        "require_preferred_industries": True,
        "reject_missing_tech": True,
        "reject_missing_revenue": True,
        "data_quality": "require-complete",
        "max_critical_unknowns": 0,
    },
}

# Confidence floors per data quality level
CONFIDENCE_FLOORS: dict[str, float] = {
    "accept-incomplete": 0.40,
    "prefer-complete": 0.60,
    "require-complete": 0.75,
}

# Company size presets
SIZE_PRESETS: dict[str, dict[str, int]] = {
    "startup": {"min": 10, "max": 100},
    "smb": {"min": 50, "max": 500},
    "mid_market": {"min": 200, "max": 2000},
    "enterprise": {"min": 1000, "max": 10000},
    "any": {"min": 1, "max": 100000},
}

# All known funding stages
ALL_FUNDING_STAGES: list[str] = [
    "pre_seed", "seed", "series_a", "series_b", "series_c",
    "series_d_plus", "private_equity", "public", "bootstrapped", "other",
]

# Competitor detection keywords (staffing industry)
COMPETITOR_KEYWORDS: list[str] = [
    "staffing", "recruiting", "recruitment", "talent acquisition", "headhunting",
    "contingency", "contract staffing", "managed services", "vendor management",
    "outsourcing", "staffing company", "recruitment firm", "staffing agency",
    "staffing solution", "talent provider", "recruitment partner",
]

# Apollo employee range buckets
APOLLO_EMPLOYEE_RANGES: list[str] = [
    "1,10", "11,20", "21,50", "51,100", "101,200",
    "201,500", "501,1000", "1001,2000", "2001,5000",
    "5001,10000", "10001,",
]

# Fields used for data completeness scoring
CRITICAL_FIELDS: list[str] = [
    "employee_count", "estimated_annual_revenue", "funding_stage",
    "tech_stack", "industry", "intent_topics",
]

# Field weights for confidence computation
FIELD_WEIGHTS: dict[str, int] = {
    "employee_count": 10,
    "estimated_annual_revenue": 10,
    "funding_stage": 8,
    "tech_stack": 8,
    "industry": 6,
    "intent_topics": 8,
}
