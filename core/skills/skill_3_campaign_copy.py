"""Skill 3 — Campaign Copy: generates email/LinkedIn variants via OpenAI."""

from __future__ import annotations

import uuid
from pathlib import Path

import structlog

from app.config import get_settings
from clients.openai_client import generate_copy
from clients.supabase_client import get_supabase_client
from services.verticals.context_builder import build_skill_context

logger = structlog.get_logger()


def _read_context_file(context_dir: Path, *parts: str) -> str:
    """Read a context file, returning empty string if missing."""
    filepath = context_dir.joinpath(*parts)
    try:
        return filepath.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        logger.debug("context_file_missing", path=str(filepath))
        return ""


async def run_skill_3(
    offer_slug: str,
    campaign_slug: str,
    offers_dir: str = "offers",
) -> dict:
    """Generate campaign copy (email + LinkedIn variants) via OpenAI.

    Args:
        offer_slug: Offer slug.
        campaign_slug: Campaign slug.
        offers_dir: Base directory for offer output files.

    Returns:
        {"variants": {"email": int, "linkedin": int}, "cost_usd": float}

    Raises:
        FileNotFoundError: If strategy.md or positioning.md is missing.
    """
    settings = get_settings()
    context_dir = Path(settings.context_dir)
    base = Path(offers_dir)

    logger.info("skill_3_start", offer_slug=offer_slug, campaign_slug=campaign_slug)

    # Read required files
    positioning_path = base / offer_slug / "positioning.md"
    strategy_path = base / offer_slug / "campaigns" / campaign_slug / "strategy.md"

    if not positioning_path.exists():
        raise FileNotFoundError(f"Positioning not found: {positioning_path}")
    if not strategy_path.exists():
        raise FileNotFoundError(f"Strategy not found: {strategy_path}")

    positioning_md = positioning_path.read_text(encoding="utf-8")
    strategy_md = strategy_path.read_text(encoding="utf-8")

    # Read copywriting context files
    email_principles = _read_context_file(context_dir, "copywriting", "email-principles.md")
    linkedin_principles = _read_context_file(context_dir, "copywriting", "linkedin-principles.md")

    # Build vertical context (try to resolve vertical from strategy or positioning)
    vertical_context = ""
    vertical_id = _resolve_vertical_id(offer_slug, campaign_slug)
    if vertical_id:
        vertical_context = build_skill_context(
            skill_id=3,
            vertical_slug=vertical_id,
            base_dir=str(context_dir / "verticals"),
        )

    # Assemble the prompt
    prompt = f"""Generate outbound copy for this campaign.

## Strategy
{strategy_md}

## Email Copywriting Principles
{email_principles}

## LinkedIn Copywriting Principles
{linkedin_principles}

Create 3 email variants and 2 LinkedIn variants. Each should reference specific signals from the strategy."""

    # Call OpenAI
    result = await generate_copy(
        prompt=prompt,
        offer_context=positioning_md,
        vertical_context=vertical_context,
    )

    email_variants = result.get("email_variants", [])
    linkedin_variants = result.get("linkedin_variants", [])
    personalization_notes = result.get("personalization_notes", "")

    # Write output files
    copy_dir = base / offer_slug / "campaigns" / campaign_slug / "copy"
    copy_dir.mkdir(parents=True, exist_ok=True)

    # Email variants
    email_md = "# Email Variants\n\n"
    for i, v in enumerate(email_variants, 1):
        name = v.get("variant_name", f"Variant {i}")
        email_md += f"## {name}\n\n**Subject:** {v.get('subject', '')}\n\n{v.get('body', '')}\n\n---\n\n"
    (copy_dir / "email-variants.md").write_text(email_md, encoding="utf-8")

    # LinkedIn variants
    linkedin_md = "# LinkedIn Variants\n\n"
    for i, v in enumerate(linkedin_variants, 1):
        name = v.get("variant_name", f"Variant {i}")
        linkedin_md += f"## {name}\n\n{v.get('body', '')}\n\n---\n\n"
    (copy_dir / "linkedin-variants.md").write_text(linkedin_md, encoding="utf-8")

    # Personalization notes
    (copy_dir / "personalization-notes.md").write_text(
        f"# Personalization Notes\n\n{personalization_notes}\n",
        encoding="utf-8",
    )

    logger.info(
        "skill_3_copy_written",
        email_count=len(email_variants),
        linkedin_count=len(linkedin_variants),
    )

    # Estimate cost (GPT-4o ~$5/1M input, $15/1M output — rough estimate)
    prompt_chars = len(prompt) + len(positioning_md) + len(vertical_context)
    cost_usd = round((prompt_chars / 4) * 5 / 1_000_000 + 0.01, 4)  # rough estimate

    # Upsert to Supabase (graceful degradation)
    try:
        db = get_supabase_client()

        # Look up campaign_id
        campaign_row = (
            db.table("campaigns")
            .select("id")
            .eq("slug", campaign_slug)
            .maybe_single()
            .execute()
        )
        campaign_id = campaign_row.data.get("id", "") if campaign_row.data else ""

        if campaign_id:
            # Upsert message variants
            for v in email_variants:
                db.table("message_variants").upsert(
                    {
                        "id": str(uuid.uuid4()),
                        "campaign_id": campaign_id,
                        "channel": "email",
                        "variant_name": v.get("variant_name", ""),
                        "subject": v.get("subject", ""),
                        "body": v.get("body", ""),
                    },
                    on_conflict="id",
                ).execute()

            for v in linkedin_variants:
                db.table("message_variants").upsert(
                    {
                        "id": str(uuid.uuid4()),
                        "campaign_id": campaign_id,
                        "channel": "linkedin",
                        "variant_name": v.get("variant_name", ""),
                        "body": v.get("body", ""),
                    },
                    on_conflict="id",
                ).execute()

            # Track cost
            db.table("tool_usage").insert(
                {
                    "id": str(uuid.uuid4()),
                    "tool": "openai",
                    "action": "generate_copy",
                    "cost_usd": cost_usd,
                    "metadata": {
                        "offer_slug": offer_slug,
                        "campaign_slug": campaign_slug,
                    },
                }
            ).execute()

        logger.info("skill_3_db_upsert", campaign_id=campaign_id)
    except Exception as exc:
        logger.warn("skill_3_db_unavailable", error=str(exc))

    return {
        "variants": {
            "email": len(email_variants),
            "linkedin": len(linkedin_variants),
        },
        "cost_usd": cost_usd,
    }


def _resolve_vertical_id(offer_slug: str, campaign_slug: str) -> str | None:
    """Try to resolve vertical_id from Supabase (campaign → offer fallback)."""
    try:
        db = get_supabase_client()
        # Try campaign first
        row = (
            db.table("campaigns")
            .select("vertical_id, offer_id, offers(default_vertical_id)")
            .eq("slug", campaign_slug)
            .maybe_single()
            .execute()
        )
        if row.data:
            vid = row.data.get("vertical_id")
            if vid:
                return vid
            offer_data = row.data.get("offers")
            if isinstance(offer_data, dict):
                return offer_data.get("default_vertical_id")
    except Exception:
        pass
    return None
