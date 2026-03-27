"""ICP Executor — runs companies through hard filters, scoring, confidence, tiering.

Pipeline: hard_filters → scoring → confidence_gate → tiering
"""

from __future__ import annotations

import re
from typing import Any

from .constants import (
    COMPETITOR_KEYWORDS,
    CONFIDENCE_FLOORS,
    CRITICAL_FIELDS,
    DIMENSION_MAX,
    FIELD_WEIGHTS,
    MAX_SCORE,
)
from .types import (
    IcpCompanyTrace,
    IcpConfidenceScore,
    IcpFilterTrace,
    IcpScoringTrace,
    NormalizedIcpRules,
)

# ---------------------------------------------------------------------------
# Hard Filters
# ---------------------------------------------------------------------------


def evaluate_hard_filters(
    company: dict[str, Any], rules: NormalizedIcpRules
) -> list[IcpFilterTrace]:
    """Run 8 sequential hard-filter gates. Short-circuits on first failure."""
    hf = rules.hard_filters
    traces: list[IcpFilterTrace] = []

    gates = [
        _gate_company_size,
        _gate_industry_excluded,
        _gate_industry_required,
        _gate_funding,
        _gate_competitor,
        _gate_tech_must_have,
        _gate_hiring_required,
        _gate_intent_required,
    ]

    for gate_fn in gates:
        trace = gate_fn(company, hf)
        traces.append(trace)
        if not trace.passed:
            break

    return traces


def _gate_company_size(
    company: dict[str, Any], hf: dict[str, Any]
) -> IcpFilterTrace:
    gate = "company_size"
    size_cfg = hf.get("company_size")
    if not size_cfg:
        return IcpFilterTrace(gate=gate, passed=True, reason="no size filter configured")

    hard_min = size_cfg.get("hardMin") or size_cfg.get("hard_min")
    hard_max = size_cfg.get("hardMax") or size_cfg.get("hard_max")
    reject_outside = size_cfg.get("rejectOutside", size_cfg.get("reject_outside", False))

    if not reject_outside:
        return IcpFilterTrace(gate=gate, passed=True, reason="rejectOutside is false")

    emp = company.get("employee_count")
    if emp is None:
        return IcpFilterTrace(gate=gate, passed=True, reason="employee_count unknown, passing")

    if hard_min is not None and emp < hard_min:
        return IcpFilterTrace(
            gate=gate, passed=False,
            reason=f"employee_count {emp} below hardMin {hard_min}",
            rule_value=hard_min, company_value=emp,
        )
    if hard_max is not None and emp > hard_max:
        return IcpFilterTrace(
            gate=gate, passed=False,
            reason=f"employee_count {emp} above hardMax {hard_max}",
            rule_value=hard_max, company_value=emp,
        )
    return IcpFilterTrace(gate=gate, passed=True, reason="within size range")


def _gate_industry_excluded(
    company: dict[str, Any], hf: dict[str, Any]
) -> IcpFilterTrace:
    gate = "industry_excluded"
    excluded = hf.get("industries", {}).get("excluded", [])
    if not excluded:
        return IcpFilterTrace(gate=gate, passed=True, reason="no excluded industries")

    industry = (company.get("industry") or "").lower()
    sic_codes = company.get("sic_codes") or []
    if isinstance(sic_codes, str):
        sic_codes = [sic_codes]

    for ex in excluded:
        ex_lower = ex.lower()
        # exact match
        if industry == ex_lower:
            return IcpFilterTrace(
                gate=gate, passed=False,
                reason=f"industry '{industry}' matches excluded '{ex}'",
                rule_value=excluded, company_value=industry,
            )
        # substring match
        if ex_lower in industry:
            return IcpFilterTrace(
                gate=gate, passed=False,
                reason=f"industry '{industry}' contains excluded substring '{ex}'",
                rule_value=excluded, company_value=industry,
            )
        # SIC code match
        if ex in sic_codes:
            return IcpFilterTrace(
                gate=gate, passed=False,
                reason=f"SIC code '{ex}' is in excluded list",
                rule_value=excluded, company_value=sic_codes,
            )

    return IcpFilterTrace(gate=gate, passed=True, reason="industry not excluded")


def _gate_industry_required(
    company: dict[str, Any], hf: dict[str, Any]
) -> IcpFilterTrace:
    gate = "industry_required"
    required = hf.get("industries", {}).get("required", [])
    if not required:
        return IcpFilterTrace(gate=gate, passed=True, reason="no required industries")

    industry = (company.get("industry") or "").lower()
    if not industry:
        return IcpFilterTrace(
            gate=gate, passed=False,
            reason="industry unknown but required industries specified",
            rule_value=required, company_value=None,
        )

    for req in required:
        if req.lower() in industry or industry in req.lower():
            return IcpFilterTrace(gate=gate, passed=True, reason=f"industry matches '{req}'")

    return IcpFilterTrace(
        gate=gate, passed=False,
        reason=f"industry '{industry}' not in required list",
        rule_value=required, company_value=industry,
    )


def _gate_funding(
    company: dict[str, Any], hf: dict[str, Any]
) -> IcpFilterTrace:
    gate = "funding"
    excluded = hf.get("funding", {}).get("excluded", [])
    required = hf.get("funding", {}).get("required", [])

    funding = company.get("funding_stage") or ""
    funding_lower = funding.lower()

    if excluded and funding_lower:
        for ex in excluded:
            if ex.lower() == funding_lower:
                return IcpFilterTrace(
                    gate=gate, passed=False,
                    reason=f"funding stage '{funding}' is excluded",
                    rule_value=excluded, company_value=funding,
                )

    if required:
        if not funding_lower:
            return IcpFilterTrace(
                gate=gate, passed=False,
                reason="funding stage unknown but required stages specified",
                rule_value=required, company_value=None,
            )
        matched = any(r.lower() == funding_lower for r in required)
        if not matched:
            return IcpFilterTrace(
                gate=gate, passed=False,
                reason=f"funding stage '{funding}' not in required list",
                rule_value=required, company_value=funding,
            )

    return IcpFilterTrace(gate=gate, passed=True, reason="funding filter passed")


def _gate_competitor(
    company: dict[str, Any], hf: dict[str, Any]
) -> IcpFilterTrace:
    gate = "competitor"
    if not hf.get("competitors"):
        return IcpFilterTrace(gate=gate, passed=True, reason="competitor filter disabled")

    fields_to_check = [
        company.get("name", ""),
        company.get("domain", ""),
        company.get("industry", ""),
    ]
    combined = " ".join(str(f) for f in fields_to_check).lower()

    for kw in COMPETITOR_KEYWORDS:
        pattern = r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pattern, combined):
            return IcpFilterTrace(
                gate=gate, passed=False,
                reason=f"competitor keyword '{kw}' found",
                rule_value=COMPETITOR_KEYWORDS, company_value=combined,
            )

    return IcpFilterTrace(gate=gate, passed=True, reason="no competitor keywords matched")


def _gate_tech_must_have(
    company: dict[str, Any], hf: dict[str, Any]
) -> IcpFilterTrace:
    gate = "tech_must_have"
    tech_cfg = hf.get("tech", {})
    if not tech_cfg:
        return IcpFilterTrace(gate=gate, passed=True, reason="no tech_must_have filter")

    keywords = tech_cfg.get("must_have", [])
    if not keywords:
        return IcpFilterTrace(gate=gate, passed=True, reason="no tech keywords specified")

    behavior = tech_cfg.get("behavior", "require-when-data-exists")
    tech_stack = company.get("tech_stack") or []
    if isinstance(tech_stack, str):
        tech_stack = [tech_stack]

    if not tech_stack:
        if behavior == "require-always":
            return IcpFilterTrace(
                gate=gate, passed=False,
                reason="tech_stack empty and behavior is require-always",
                rule_value=keywords, company_value=None,
            )
        # require-when-data-exists: no data means pass
        return IcpFilterTrace(gate=gate, passed=True, reason="no tech data, skipping check")

    stack_lower = [t.lower() for t in tech_stack]
    for kw in keywords:
        if kw.lower() not in stack_lower:
            return IcpFilterTrace(
                gate=gate, passed=False,
                reason=f"required tech '{kw}' not found in stack",
                rule_value=keywords, company_value=tech_stack,
            )

    return IcpFilterTrace(gate=gate, passed=True, reason="all required tech found")


def _gate_hiring_required(
    company: dict[str, Any], hf: dict[str, Any]
) -> IcpFilterTrace:
    gate = "hiring_required"
    if not hf.get("hiring_required"):
        return IcpFilterTrace(gate=gate, passed=True, reason="hiring not required")

    status = (company.get("hiring_status") or "").lower()
    if status == "likely":
        return IcpFilterTrace(gate=gate, passed=True, reason="hiring_status is likely")

    return IcpFilterTrace(
        gate=gate, passed=False,
        reason=f"hiring_status is '{status}', expected 'likely'",
        rule_value="likely", company_value=status,
    )


def _gate_intent_required(
    company: dict[str, Any], hf: dict[str, Any]
) -> IcpFilterTrace:
    gate = "intent_required"
    if not hf.get("intent_required"):
        return IcpFilterTrace(gate=gate, passed=True, reason="intent not required")

    topics = company.get("intent_topics") or []
    if isinstance(topics, str):
        topics = [topics]

    if topics:
        return IcpFilterTrace(gate=gate, passed=True, reason="intent topics present")

    return IcpFilterTrace(
        gate=gate, passed=False,
        reason="no intent topics found but intent is required",
        rule_value=True, company_value=None,
    )


# ---------------------------------------------------------------------------
# Scoring — 8 dimensions
# ---------------------------------------------------------------------------


def score_company_icp(
    company: dict[str, Any], rules: NormalizedIcpRules
) -> IcpScoringTrace:
    """Score a company across 8 ICP dimensions."""
    sc = rules.scoring

    dimensions: dict[str, float] = {
        "hiring_signal": _score_hiring_signal(company, sc),
        "company_size": _score_company_size(company, sc),
        "funding": _score_funding(company, sc),
        "revenue": _score_revenue(company, sc),
        "tech_stack": _score_tech(company, sc),
        "industry": _score_industry(company, rules),
        "domain": _score_domain(company, sc),
        "intent": _score_intent(company, sc),
    }

    total = sum(dimensions.values())
    zero_dims = [k for k, v in dimensions.items() if v == 0]
    data_max = compute_data_available_max(company, rules)

    return IcpScoringTrace(
        dimensions=dimensions,
        total=total,
        max_possible=data_max,
        threshold=rules.threshold,
        zero_dimensions=zero_dims,
        missing_points=data_max - total,
    )


def _score_hiring_signal(company: dict[str, Any], sc: dict[str, Any]) -> float:
    """0-40 pts: freshnessWeight * intensityWeight * max."""
    hiring_cfg = sc.get("hiringSignal") or sc.get("hiring_signal") or {}
    freshness = hiring_cfg.get("freshnessWeight", hiring_cfg.get("freshness_weight", 1.0))
    intensity = hiring_cfg.get("intensityWeight", hiring_cfg.get("intensity_weight", 1.0))

    status = (company.get("hiring_status") or "").lower()
    if status != "likely":
        return 0.0

    return min(DIMENSION_MAX["hiring_signal"], DIMENSION_MAX["hiring_signal"] * freshness * intensity)


def _score_company_size(company: dict[str, Any], sc: dict[str, Any]) -> float:
    """0-50 pts: ideal=50, acceptable=30, partial=15, outside=0."""
    size_cfg = sc.get("companySize") or sc.get("company_size") or {}
    emp = company.get("employee_count")
    if emp is None:
        return 0.0

    # Normalizer outputs: ideal_min, ideal_max, acceptable_max, partial_min
    ideal_min = size_cfg.get("ideal_min", 0)
    ideal_max = size_cfg.get("ideal_max", 0)
    acceptable_max = size_cfg.get("acceptable_max", 0)
    partial_min = size_cfg.get("partial_min", 0)

    if ideal_min and ideal_max and ideal_min <= emp <= ideal_max:
        return 50.0
    if ideal_max and acceptable_max and ideal_max < emp <= acceptable_max:
        return 30.0
    if partial_min is not None and ideal_min and partial_min <= emp < ideal_min:
        return 15.0

    return 0.0


def _score_funding(company: dict[str, Any], sc: dict[str, Any]) -> float:
    """0-30 pts: preferred=30, acceptable=15."""
    fund_cfg = sc.get("funding") or {}
    stage = (company.get("funding_stage") or "").lower()
    if not stage:
        return 0.0

    preferred = [s.lower() for s in fund_cfg.get("preferred", [])]
    acceptable = [s.lower() for s in fund_cfg.get("acceptable", [])]

    if stage in preferred:
        return 30.0
    if stage in acceptable:
        return 15.0
    return 0.0


def _score_revenue(company: dict[str, Any], sc: dict[str, Any]) -> float:
    """0-20 pts: actual revenue=20, inferred=10."""
    rev = company.get("estimated_annual_revenue")
    if rev is not None:
        return 20.0

    inferred = company.get("inferred_revenue")
    if inferred is not None:
        return 10.0

    return 0.0


def _score_tech(company: dict[str, Any], sc: dict[str, Any]) -> float:
    """0-45 pts: 15 per preferred match, -5 per avoided, capped at 0."""
    tech_cfg = sc.get("techStack") or sc.get("tech_stack") or {}
    stack = company.get("tech_stack") or []
    if isinstance(stack, str):
        stack = [stack]
    if not stack:
        return 0.0

    stack_lower = {t.lower() for t in stack}
    preferred = [p.lower() for p in tech_cfg.get("preferred", [])]
    avoided = [a.lower() for a in tech_cfg.get("avoided", [])]

    score = 0.0
    for p in preferred:
        if p in stack_lower:
            score += 15.0
    for a in avoided:
        if a in stack_lower:
            score -= 5.0

    return max(0.0, min(score, float(DIMENSION_MAX["tech_stack"])))


def _score_industry(company: dict[str, Any], rules: NormalizedIcpRules) -> float:
    """0-15 pts: boostMultiplier when strict + requirePreferredIndustries."""
    sc = rules.scoring
    ind_cfg = sc.get("industry") or {}
    enforcement = rules.enforcement

    industry = (company.get("industry") or "").lower()
    if not industry:
        return 0.0

    preferred = [i.lower() for i in ind_cfg.get("preferred", [])]
    if not preferred:
        return 0.0

    matched = any(p in industry or industry in p for p in preferred)
    if not matched:
        return 0.0

    boost = ind_cfg.get("boostMultiplier", ind_cfg.get("boost_multiplier", 1.0))
    require_pref = enforcement.get("require_preferred_industries", False)

    base = float(DIMENSION_MAX["industry"])
    if require_pref:
        return min(base, base * boost)
    return base


def _score_domain(company: dict[str, Any], sc: dict[str, Any]) -> float:
    """0-15 pts: domain presence check."""
    domain_cfg = sc.get("domain") or {}
    preferred = [d.lower() for d in domain_cfg.get("preferred", [])]
    if not preferred:
        # If no domain preferences configured, give base score if domain exists
        if company.get("domain"):
            return float(DIMENSION_MAX["domain"])
        return 0.0

    company_domain = (company.get("domain") or "").lower()
    if not company_domain:
        return 0.0

    for p in preferred:
        if p in company_domain or company_domain.endswith(p):
            return float(DIMENSION_MAX["domain"])

    return 0.0


def _score_intent(company: dict[str, Any], sc: dict[str, Any]) -> float:
    """0-35 pts: base 20 + 5 per additional topic, 60% reduction if below minScore."""
    intent_cfg = sc.get("intent") or {}
    topics = company.get("intent_topics") or []
    if isinstance(topics, str):
        topics = [topics]
    if not topics:
        return 0.0

    base = 20.0
    additional = min(len(topics) - 1, 3) * 5.0  # max 3 additional = 15 pts
    score = base + additional

    min_score = intent_cfg.get("minScore", intent_cfg.get("min_score", 0.0))
    intent_score = company.get("intent_score", 100.0)
    if min_score > 0 and intent_score < min_score:
        score *= 0.4  # 60% reduction

    return min(score, float(DIMENSION_MAX["intent"]))


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------


def compute_confidence(
    company: dict[str, Any], rules: NormalizedIcpRules
) -> IcpConfidenceScore:
    """Assess data quality confidence for a company."""
    critical_unknowns = 0
    fields_with_data = 0
    total_fields = len(CRITICAL_FIELDS)

    for field in CRITICAL_FIELDS:
        val = company.get(field)
        has_data = val is not None and val != "" and val != []
        if has_data:
            fields_with_data += 1
        else:
            critical_unknowns += 1

    data_completeness = (fields_with_data / total_fields) * 100.0 if total_fields > 0 else 0.0

    # Weighted match strength
    total_weight = sum(FIELD_WEIGHTS.values())
    weighted_present = sum(
        FIELD_WEIGHTS.get(f, 0)
        for f in CRITICAL_FIELDS
        if _has_value(company, f)
    )
    match_strength = (weighted_present / total_weight) * 100.0 if total_weight > 0 else 0.0

    # Check against confidence floor
    data_quality = rules.data_quality
    floor = CONFIDENCE_FLOORS.get(data_quality, 0.40)
    max_unknowns = rules.max_critical_unknowns

    overall = data_completeness
    meets = (
        critical_unknowns <= max_unknowns
        and (data_completeness / 100.0) >= floor
    )

    return IcpConfidenceScore(
        overall=overall,
        meets_requirement=meets,
        critical_unknowns=critical_unknowns,
        data_completeness=data_completeness,
        match_strength=match_strength,
    )


def _has_value(company: dict[str, Any], field: str) -> bool:
    val = company.get(field)
    if val is None:
        return False
    if isinstance(val, str) and val == "":
        return False
    if isinstance(val, list) and len(val) == 0:
        return False
    return True


# ---------------------------------------------------------------------------
# Tiering
# ---------------------------------------------------------------------------


def determine_tier(score: float, threshold: float) -> str | None:
    """Determine tier based on score vs threshold.

    A: score >= threshold * 1.5
    B: score >= threshold * 1.0
    C: score >= threshold * 0.65
    None: below C
    """
    if threshold <= 0:
        return None
    if score >= threshold * 1.5:
        return "A"
    if score >= threshold * 1.0:
        return "B"
    if score >= threshold * 0.65:
        return "C"
    return None


# ---------------------------------------------------------------------------
# Data Available Max
# ---------------------------------------------------------------------------


def compute_data_available_max(
    company: dict[str, Any], rules: NormalizedIcpRules
) -> float:
    """Reduce max possible score when company data is missing for a dimension."""
    max_score = float(MAX_SCORE)

    field_to_dimension = {
        "employee_count": "company_size",
        "funding_stage": "funding",
        "estimated_annual_revenue": "revenue",
        "tech_stack": "tech_stack",
        "industry": "industry",
        "intent_topics": "intent",
    }

    for field, dim in field_to_dimension.items():
        if not _has_value(company, field):
            # Also check inferred_revenue for revenue dimension
            if dim == "revenue" and _has_value(company, "inferred_revenue"):
                continue
            max_score -= DIMENSION_MAX.get(dim, 0)

    return max_score


# ---------------------------------------------------------------------------
# Full Pipeline
# ---------------------------------------------------------------------------


def execute_icp_pipeline(
    rules: NormalizedIcpRules, companies: list[dict[str, Any]]
) -> dict[str, Any]:
    """Execute the full ICP pipeline: hard filters -> scoring -> confidence -> tiering.

    Returns dict with keys: qualified, rejected, traces.
    """
    qualified: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    traces: list[IcpCompanyTrace] = []

    for company in companies:
        trace = IcpCompanyTrace(
            company_id=str(company.get("id", "")),
            apollo_id=company.get("apollo_id"),
            company_name=company.get("name", ""),
        )

        # Stage 1: Hard filters
        filter_traces = evaluate_hard_filters(company, rules)
        trace.hard_filters = filter_traces

        if filter_traces and not filter_traces[-1].passed:
            trace.outcome = "rejected-hard-filter"
            rejected.append(company)
            traces.append(trace)
            continue

        # Stage 2: Scoring
        scoring_trace = score_company_icp(company, rules)
        trace.scoring = scoring_trace

        # Stage 3: Confidence
        confidence = compute_confidence(company, rules)
        trace.confidence = confidence

        if not confidence.meets_requirement:
            trace.outcome = "rejected-confidence"
            rejected.append(company)
            traces.append(trace)
            continue

        # Stage 4: Tiering
        tier = determine_tier(scoring_trace.total, rules.threshold)

        if tier is None:
            trace.outcome = "rejected-scoring"
            rejected.append(company)
            traces.append(trace)
            continue

        trace.tier = tier  # type: ignore[assignment]
        trace.outcome = "qualified"
        qualified.append(company)
        traces.append(trace)

    return {
        "qualified": qualified,
        "rejected": rejected,
        "traces": traces,
    }
