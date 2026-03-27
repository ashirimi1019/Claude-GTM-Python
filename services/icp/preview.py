"""ICP Preview — pure function for previewing ICP pipeline results without DB/Apollo.

Used by the ICP Builder UI to show qualification stats before committing.
"""

from __future__ import annotations

from typing import Any

from .executor import execute_icp_pipeline
from .normalizer import normalize_for_search_stage, normalize_icp_profile
from .types import IcpCompanyTrace, IcpProfile


def run_icp_preview(
    profile: dict[str, Any],
    companies: list[dict[str, Any]],
    geography_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the ICP pipeline in preview mode (no DB, no Apollo).

    Uses normalize_for_search_stage() for Stage 1 modeling (broad).
    Then runs execute_icp_pipeline with user strictness for Stage 2.

    Returns summary stats, rejection breakdown, tier distribution, etc.
    """
    icp_profile = IcpProfile.model_validate(profile)

    # Apply geography override if provided
    if geography_override is not None:
        if icp_profile.hard_filters is None:
            from .types import GeographyFilter, HardFiltersConfig
            icp_profile.hard_filters = HardFiltersConfig(
                geography=GeographyFilter(**geography_override)
            )
        elif icp_profile.hard_filters.geography is None:
            from .types import GeographyFilter
            icp_profile.hard_filters.geography = GeographyFilter(**geography_override)
        else:
            geo = icp_profile.hard_filters.geography
            if "allowedCountries" in geography_override or "allowed_countries" in geography_override:
                geo.allowed_countries = geography_override.get(
                    "allowed_countries", geography_override.get("allowedCountries", [])
                )
            if "allowedUsStates" in geography_override or "allowed_us_states" in geography_override:
                geo.allowed_us_states = geography_override.get(
                    "allowed_us_states", geography_override.get("allowedUsStates")
                )

    # Stage 1: broad rules (search stage)
    stage1_rules = normalize_for_search_stage(icp_profile)
    stage1_result = execute_icp_pipeline(stage1_rules, companies)

    # Stage 2: user strictness rules on Stage 1 qualified
    stage2_rules = normalize_icp_profile(icp_profile)
    stage2_result = execute_icp_pipeline(stage2_rules, stage1_result["qualified"])

    # Build response
    total = len(companies)
    stage1_qualified = len(stage1_result["qualified"])
    stage2_qualified = len(stage2_result["qualified"])
    stage2_rejected = len(stage2_result["rejected"])

    # Rejection breakdown
    rejection_breakdown = _build_rejection_breakdown(
        stage1_result["traces"], stage2_result["traces"]
    )

    # Top rejection reasons
    top_reasons = _build_top_rejection_reasons(
        stage1_result["traces"], stage2_result["traces"]
    )

    # Tier distribution from Stage 2 qualified
    tier_dist = _build_tier_distribution(stage2_result["traces"])

    # Confidence stats from Stage 2
    confidence_stats = _build_confidence_stats(stage2_result["traces"])

    # Score stats from Stage 2
    score_stats = _build_score_stats(stage2_result["traces"])

    # Sample traces (up to 5 from each outcome)
    sample_traces = _build_sample_traces(stage1_result["traces"], stage2_result["traces"])

    return {
        "summary": {
            "totalCompanies": total,
            "qualified": stage2_qualified,
            "rejected": total - stage2_qualified,
            "qualificationRate": round(stage2_qualified / total * 100, 1) if total > 0 else 0.0,
        },
        "rejectionBreakdown": rejection_breakdown,
        "topRejectionReasons": top_reasons,
        "tierDistribution": tier_dist,
        "confidenceStats": confidence_stats,
        "scoreStats": score_stats,
        "effectiveConfig": {
            "stage1_threshold": stage1_rules.threshold,
            "stage2_threshold": stage2_rules.threshold,
            "strictness": icp_profile.strictness.level,
        },
        "sampleTraces": sample_traces,
        "twoStageInfo": {
            "stage1_input": total,
            "stage1_qualified": stage1_qualified,
            "stage1_rejected": total - stage1_qualified,
            "stage2_input": stage1_qualified,
            "stage2_qualified": stage2_qualified,
            "stage2_rejected": stage2_rejected,
        },
    }


def _build_rejection_breakdown(
    stage1_traces: list[IcpCompanyTrace],
    stage2_traces: list[IcpCompanyTrace],
) -> dict[str, int]:
    breakdown: dict[str, int] = {}
    for trace in stage1_traces:
        if trace.outcome != "qualified":
            breakdown[trace.outcome] = breakdown.get(trace.outcome, 0) + 1
    for trace in stage2_traces:
        if trace.outcome != "qualified":
            breakdown[trace.outcome] = breakdown.get(trace.outcome, 0) + 1
    return breakdown


def _build_top_rejection_reasons(
    stage1_traces: list[IcpCompanyTrace],
    stage2_traces: list[IcpCompanyTrace],
) -> list[dict[str, Any]]:
    reason_counts: dict[str, int] = {}
    for traces in [stage1_traces, stage2_traces]:
        for trace in traces:
            if trace.outcome == "qualified":
                continue
            if trace.outcome == "rejected-hard-filter" and trace.hard_filters:
                failed = [f for f in trace.hard_filters if not f.passed]
                if failed:
                    reason = failed[-1].reason
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
            elif trace.outcome in ("rejected-scoring", "rejected-confidence"):
                reason_counts[trace.outcome] = reason_counts.get(trace.outcome, 0) + 1

    sorted_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)
    return [{"reason": r, "count": c} for r, c in sorted_reasons[:10]]


def _build_tier_distribution(traces: list[IcpCompanyTrace]) -> dict[str, int]:
    dist: dict[str, int] = {"A": 0, "B": 0, "C": 0}
    for trace in traces:
        if trace.tier in dist:
            dist[trace.tier] += 1
    return dist


def _build_confidence_stats(traces: list[IcpCompanyTrace]) -> dict[str, Any]:
    values = [t.confidence.overall for t in traces if t.confidence is not None]
    if not values:
        return {"min": 0.0, "max": 0.0, "avg": 0.0, "count": 0}
    return {
        "min": round(min(values), 1),
        "max": round(max(values), 1),
        "avg": round(sum(values) / len(values), 1),
        "count": len(values),
    }


def _build_score_stats(traces: list[IcpCompanyTrace]) -> dict[str, Any]:
    values = [t.scoring.total for t in traces if t.scoring is not None]
    if not values:
        return {"min": 0.0, "max": 0.0, "avg": 0.0, "count": 0}
    return {
        "min": round(min(values), 1),
        "max": round(max(values), 1),
        "avg": round(sum(values) / len(values), 1),
        "count": len(values),
    }


def _build_sample_traces(
    stage1_traces: list[IcpCompanyTrace],
    stage2_traces: list[IcpCompanyTrace],
) -> dict[str, list[dict[str, Any]]]:
    samples: dict[str, list[dict[str, Any]]] = {
        "qualified": [],
        "rejected-hard-filter": [],
        "rejected-scoring": [],
        "rejected-confidence": [],
    }

    all_traces = list(stage1_traces) + list(stage2_traces)
    for trace in all_traces:
        bucket = trace.outcome
        if bucket in samples and len(samples[bucket]) < 5:
            samples[bucket].append(trace.model_dump())

    return samples
