"""Personalization services — token replacement for email/LinkedIn copy."""

from __future__ import annotations

from typing import Any


def personalize_email_body(
    template: str,
    contact: dict[str, Any],
    company: dict[str, Any],
    campaign: dict[str, Any] | None = None,
) -> str:
    """Replace tokens in an email template with contact/company data.

    Supported tokens: {firstName}, {lastName}, {companyName}, {title},
    {industry}, {signal}, {campaignName}
    """
    replacements = {
        "{firstName}": contact.get("first_name") or "",
        "{lastName}": contact.get("last_name") or "",
        "{companyName}": company.get("name") or "",
        "{title}": contact.get("title") or "",
        "{industry}": company.get("industry") or "",
        "{signal}": _extract_signal(company),
        "{campaignName}": (campaign or {}).get("title") or "",
    }

    result = template
    for token, value in replacements.items():
        result = result.replace(token, value)

    return result


def personalize_linkedin_message(
    template: str,
    contact: dict[str, Any],
    company: dict[str, Any],
) -> str:
    """Replace tokens in a LinkedIn message template."""
    replacements = {
        "{firstName}": contact.get("first_name") or "",
        "{lastName}": contact.get("last_name") or "",
        "{companyName}": company.get("name") or "",
        "{title}": contact.get("title") or "",
        "{industry}": company.get("industry") or "",
        "{signal}": _extract_signal(company),
    }

    result = template
    for token, value in replacements.items():
        result = result.replace(token, value)

    return result


def build_signal_reference(evidence: dict[str, Any]) -> str:
    """Generate a natural signal reference sentence from hiring evidence.

    Example: "I noticed you recently posted a Python Developer position"
    """
    signal_name = evidence.get("signal_name") or ""
    signal_type = evidence.get("signal_type") or "other"

    if signal_type == "job_posting" and signal_name:
        return f"I noticed you recently posted a {signal_name} position"
    elif signal_type == "recent_funding":
        amount = evidence.get("details", {}).get("amount")
        if amount:
            return f"Congratulations on the recent ${amount:,.0f} funding round"
        return "Congratulations on the recent funding round"
    elif signal_type == "growth_metrics":
        return f"I noticed {signal_name} growth at your company"
    elif signal_type == "skill_increase":
        return f"I noticed growing demand for {signal_name} skills on your team"
    elif signal_type == "bombora_intent":
        return f"I noticed your company is actively researching {signal_name}"
    else:
        return f"I noticed some interesting activity — {signal_name}" if signal_name else ""


def _extract_signal(company: dict[str, Any]) -> str:
    """Extract the best signal reference from a company's hiring_signals."""
    signals = company.get("hiring_signals") or {}
    if not signals:
        return ""

    # Pick the signal with highest intensity
    best_signal = ""
    best_intensity = 0
    for name, details in signals.items():
        intensity = details.get("intensity", 0) if isinstance(details, dict) else 0
        if intensity > best_intensity:
            best_intensity = intensity
            best_signal = name

    return best_signal
