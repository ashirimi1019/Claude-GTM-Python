"""LLM reasoning wrapper — all agent OpenAI calls go through here."""

from __future__ import annotations

import json
from typing import Any

import structlog

from app.config import get_settings

logger = structlog.get_logger()


async def reason_about(agent_name: str, prompt: str, context: str) -> dict[str, Any]:
    """Send a reasoning request to OpenAI and return structured recommendations.

    Args:
        agent_name: Name of the calling agent (for logging).
        prompt: The agent-specific reasoning prompt.
        context: Campaign snapshot / prior context serialized as text.

    Returns:
        Parsed JSON dict with 'recommendations' list and 'reasoning' string.
    """
    from openai import AsyncOpenAI

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    system_prompt = f"""You are {agent_name}, an AI agent in a multi-agent outbound campaign system.

Analyze the campaign context and provide structured recommendations.

{context}

Respond in JSON format:
{{
    "recommendations": [
        {{
            "domain": "icp|copy|lead|workflow",
            "action": "short description of what to do",
            "params": {{}},
            "confidence": 0.0-1.0,
            "reasoning": "why this recommendation",
            "risk_level": "safe|moderate|risky"
        }}
    ],
    "reasoning": "overall analysis summary"
}}"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        result = json.loads(content)

        logger.info(
            "Agent reasoning complete",
            agent=agent_name,
            recommendations=len(result.get("recommendations", [])),
            model=response.model,
            tokens=response.usage.total_tokens if response.usage else 0,
        )

        return result

    except Exception as e:
        logger.error("Agent reasoning failed", agent=agent_name, error=str(e))
        return {"recommendations": [], "reasoning": f"LLM reasoning failed: {e}"}
