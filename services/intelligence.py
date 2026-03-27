"""Intelligence services — OpenAI company classification + contact segmentation."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()

# Segment assignment rules
DECISION_MAKER_SENIORITIES = {"vp", "director", "head", "c_suite", "founder", "owner"}
IMPLEMENTER_SENIORITIES = {"individual_contributor", "senior", "staff", "principal"}
MANAGER_SENIORITIES = {"manager"}


def assign_contact_segment(
    contact: dict[str, Any],
    company: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assign a contact to a segment based on seniority and department.

    Returns:
        Dict with 'segment', 'seniority_group', 'decision_maker_score'.
    """
    seniority = (contact.get("seniority") or "other").lower().strip()
    department = (contact.get("department") or "other").lower().strip()
    title = (contact.get("title") or "").lower()

    # Determine seniority group
    if seniority in DECISION_MAKER_SENIORITIES or _is_executive_title(title):
        seniority_group = "executive"
        segment = "decision_maker"
        decision_maker_score = 0.9
    elif seniority in MANAGER_SENIORITIES:
        seniority_group = "manager"
        segment = "influencer"
        decision_maker_score = 0.6
    elif seniority in IMPLEMENTER_SENIORITIES:
        seniority_group = "individual"
        segment = "implementer"
        decision_maker_score = 0.3
    else:
        seniority_group = "other"
        segment = "other"
        decision_maker_score = 0.1

    # Boost for engineering/data departments (our target buyers)
    if department in {"engineering", "data", "technology", "it"}:
        decision_maker_score = min(decision_maker_score + 0.1, 1.0)

    return {
        "segment": segment,
        "seniority_group": seniority_group,
        "decision_maker_score": round(decision_maker_score, 2),
    }


def _is_executive_title(title: str) -> bool:
    """Check if a title indicates executive/decision-maker level."""
    executive_keywords = [
        "cto", "cio", "ceo", "coo", "chief", "vice president", "vp",
        "svp", "evp", "head of", "director of", "founder", "co-founder",
        "partner", "president", "gm", "general manager",
    ]
    return any(kw in title for kw in executive_keywords)


async def classify_company_by_openai(
    company: dict[str, Any],
    context: str = "",
    openai_client: Any | None = None,
) -> dict[str, Any]:
    """Classify a company using OpenAI for buyer persona and fit.

    Args:
        company: Company dict with name, industry, employee_count, etc.
        context: Additional context (e.g., vertical info).
        openai_client: AsyncOpenAI client instance.

    Returns:
        Dict with 'classification', 'industry', 'growth_stage', 'recommendation'.
    """
    if openai_client is None:
        # Return a basic rule-based classification as fallback
        return _rule_based_classification(company)

    from openai import AsyncOpenAI

    client = openai_client if isinstance(openai_client, AsyncOpenAI) else openai_client

    prompt = f"""Classify this company for a staffing/consulting sales campaign.

Company: {company.get('name', 'Unknown')}
Industry: {company.get('industry', 'Unknown')}
Employees: {company.get('employee_count', 'Unknown')}
Funding: {company.get('funding_stage', 'Unknown')}
Tech Stack: {', '.join(company.get('tech_stack', []))}

{context}

Respond in JSON:
{{"classification": "high-fit|moderate-fit|low-fit", "industry": "...",\
 "growth_stage": "...", "recommendation": "..."}}"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        import json
        return json.loads(response.choices[0].message.content or "{}")
    except Exception as e:
        logger.warn("OpenAI classification failed, using rule-based", error=str(e))
        return _rule_based_classification(company)


def _rule_based_classification(company: dict[str, Any]) -> dict[str, Any]:
    """Fallback rule-based company classification."""
    employee_count = company.get("employee_count") or 0
    industry = company.get("industry") or "Unknown"

    if 100 <= employee_count <= 5000:
        classification = "high-fit"
    elif 50 <= employee_count <= 10000:
        classification = "moderate-fit"
    else:
        classification = "low-fit"

    return {
        "classification": classification,
        "industry": industry,
        "growth_stage": "unknown",
        "recommendation": f"{'Strong' if classification == 'high-fit' else 'Review'} candidate based on company size",
    }
