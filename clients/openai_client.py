"""OpenAI client — copy generation, classification, personalization."""

from __future__ import annotations

import json
from typing import Any

import structlog

from app.config import get_settings

logger = structlog.get_logger()


async def generate_copy(
    prompt: str,
    offer_context: str = "",
    vertical_context: str = "",
) -> dict[str, Any]:
    """Generate email and LinkedIn copy variants via OpenAI.

    Args:
        prompt: The copy generation prompt (from context/copywriting/*.md).
        offer_context: Offer positioning context.
        vertical_context: Vertical-specific messaging context.

    Returns:
        Dict with 'email_variants', 'linkedin_variants', 'personalization_notes'.
    """
    from openai import AsyncOpenAI

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    system_prompt = f"""You are an expert B2B copywriter for staffing/consulting outbound campaigns.

{vertical_context}

{offer_context}

Generate copy that:
1. References specific hiring signals (never generic)
2. Leads with the prospect's problem, not your solution
3. Is concise (under 150 words for email, under 300 chars for LinkedIn)
4. Has a clear, low-friction CTA

Respond in JSON format:
{{
    "email_variants": [
        {{"subject": "...", "body": "...", "variant_name": "..."}}
    ],
    "linkedin_variants": [
        {{"body": "...", "variant_name": "..."}}
    ],
    "personalization_notes": "..."
}}"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        result = json.loads(content)

        logger.info(
            "Copy generated",
            email_variants=len(result.get("email_variants", [])),
            linkedin_variants=len(result.get("linkedin_variants", [])),
            model=response.model,
            tokens=response.usage.total_tokens if response.usage else 0,
        )

        return result

    except Exception as e:
        logger.error("OpenAI copy generation failed", error=str(e))
        raise


async def classify_company(
    company: dict[str, Any],
    context: str = "",
) -> dict[str, Any]:
    """Classify a company for buyer persona fit via OpenAI."""
    from openai import AsyncOpenAI

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    prompt = f"""Classify this company for a staffing/consulting sales campaign.

Company: {company.get('name', 'Unknown')}
Industry: {company.get('industry', 'Unknown')}
Employees: {company.get('employee_count', 'Unknown')}
Funding: {company.get('funding_stage', 'Unknown')}
Tech Stack: {', '.join(company.get('tech_stack', []))}

{context}

Respond in JSON: {{"classification": "high-fit|moderate-fit|low-fit", "industry": "...", "growth_stage": "...", "recommendation": "..."}}"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        return json.loads(response.choices[0].message.content or "{}")
    except Exception as e:
        logger.warn("OpenAI classification failed", error=str(e))
        return {"classification": "unknown", "recommendation": "Manual review needed"}


async def generate_personalization(
    contact: dict[str, Any],
    company: dict[str, Any],
    signal: dict[str, Any],
) -> str:
    """Generate a personalized opener for a contact based on hiring signals."""
    from openai import AsyncOpenAI

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    prompt = f"""Write a natural, one-sentence personalized opener for an outbound email.

Contact: {contact.get('first_name', '')} {contact.get('last_name', '')}, {contact.get('title', '')}
Company: {company.get('name', '')} ({company.get('industry', '')})
Signal: {signal.get('signal_name', '')} ({signal.get('signal_type', '')})

Requirements:
- Reference the specific signal naturally
- Don't be generic or salesy
- Under 30 words
- Professional but warm tone"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100,
        )

        return (response.choices[0].message.content or "").strip()
    except Exception as e:
        logger.warn("OpenAI personalization failed", error=str(e))
        return ""
