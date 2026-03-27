"""Guardrails validators — Tier 2 (automated) and Tier 3 (human approval)."""

from __future__ import annotations

import re


def validate_copy_tier2(variant: dict) -> dict:
    """Tier 2: Automated checks on generated copy."""
    errors = []
    body = variant.get("body", "")
    subject = variant.get("subject", "")

    # Check length limits
    if len(body) > 2000:
        errors.append("Body exceeds 2000 character limit")
    if subject and len(subject) > 200:
        errors.append("Subject exceeds 200 character limit")

    # Check for placeholder tokens left in
    placeholders = re.findall(r'\{[a-zA-Z_]+\}', body)
    allowed_placeholders = {
        '{firstName}', '{lastName}', '{companyName}',
        '{title}', '{industry}', '{signal}', '{campaignName}',
    }
    unfilled = [p for p in placeholders if p not in allowed_placeholders]
    if unfilled:
        errors.append(f"Unknown placeholders found: {unfilled}")

    # Check for hallucination markers
    hallucination_phrases = [
        "as an ai",
        "i don't have access",
        "i cannot",
        "based on my training",
    ]
    for phrase in hallucination_phrases:
        if phrase in body.lower():
            errors.append(f"Hallucination marker detected: '{phrase}'")

    return {"valid": len(errors) == 0, "errors": errors, "tier": 2}


def validate_copy_tier3(variant: dict) -> dict:
    """Tier 3: Flags copy for human approval."""
    flags = []
    body = variant.get("body", "")

    # Flag aggressive CTAs
    aggressive_phrases = ["act now", "limited time", "don't miss out", "urgent"]
    for phrase in aggressive_phrases:
        if phrase in body.lower():
            flags.append(f"Aggressive CTA detected: '{phrase}'")

    # Flag competitor mentions
    if any(word in body.lower() for word in ["competitor", "vs ", "versus", "better than"]):
        flags.append("Competitor comparison detected — requires review")

    needs_approval = len(flags) > 0
    return {"needs_approval": needs_approval, "flags": flags, "tier": 3}
