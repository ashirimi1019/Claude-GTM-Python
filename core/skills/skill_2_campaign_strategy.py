"""Skill 2 — Campaign Strategy: generates strategy.md and upserts to Supabase."""

from __future__ import annotations

import uuid
from pathlib import Path

import structlog

from app.config import get_settings
from clients.supabase_client import get_supabase_client
from models.campaign import CampaignCreate
from services.verticals.context_builder import build_skill_context

logger = structlog.get_logger()


async def run_skill_2(config: dict, offers_dir: str = "offers") -> dict:
    """Create a campaign strategy for an existing offer.

    Args:
        config: Dict with keys: offer_slug, name, vertical_id,
                allowed_countries, allowed_us_states.
        offers_dir: Base directory for offer output files.

    Returns:
        {"slug": str, "strategy_path": str}

    Raises:
        FileNotFoundError: If offer positioning.md does not exist.
    """
    offer_slug = config["offer_slug"]
    campaign = CampaignCreate(
        offer_slug=offer_slug,
        name=config["name"],
        vertical_id=config.get("vertical_id") or None,
        allowed_countries=config.get("allowed_countries"),
        allowed_us_states=config.get("allowed_us_states"),
    )
    campaign_slug = campaign.slug
    logger.info("skill_2_start", offer_slug=offer_slug, campaign_slug=campaign_slug)

    # Validate offer exists
    positioning_path = Path(offers_dir) / offer_slug / "positioning.md"
    if not positioning_path.exists():
        raise FileNotFoundError(
            f"Offer positioning not found: {positioning_path}. Run Skill 1 first."
        )
    positioning_md = positioning_path.read_text(encoding="utf-8")

    # Build campaign directory
    campaign_dir = Path(offers_dir) / offer_slug / "campaigns" / campaign_slug
    campaign_dir.mkdir(parents=True, exist_ok=True)

    # Assemble strategy content
    strategy_parts: list[str] = [
        f"# Campaign: {config['name']}\n",
        f"## Offer: {offer_slug}\n",
        f"\n## Offer Positioning\n\n{positioning_md}\n",
    ]

    # Add vertical context if available
    if campaign.vertical_id:
        settings = get_settings()
        vertical_context = build_skill_context(
            skill_id=2,
            vertical_slug=campaign.vertical_id,
            base_dir=str(Path(settings.context_dir) / "verticals"),
        )
        if vertical_context:
            strategy_parts.append(f"\n## Vertical Context\n\n{vertical_context}\n")

    if campaign.allowed_countries:
        strategy_parts.append(
            f"\n## Target Geography\n\nCountries: {', '.join(campaign.allowed_countries)}\n"
        )
    if campaign.allowed_us_states:
        strategy_parts.append(f"US States: {', '.join(campaign.allowed_us_states)}\n")

    strategy_md = "\n".join(part for part in strategy_parts if part)
    strategy_path = campaign_dir / "strategy.md"
    strategy_path.write_text(strategy_md, encoding="utf-8")
    logger.info("skill_2_strategy_written", path=str(strategy_path))

    # Upsert to Supabase (graceful degradation)
    try:
        db = get_supabase_client()
        # Look up offer_id from slug
        offer_row = (
            db.table("offers").select("id").eq("slug", offer_slug).single().execute()
        )
        offer_id = offer_row.data.get("id", "") if offer_row.data else ""

        db.table("campaigns").upsert(
            {
                "id": str(uuid.uuid4()),
                "offer_id": offer_id,
                "slug": campaign_slug,
                "title": config["name"],
                "vertical_id": campaign.vertical_id,
                "status": "draft",
                "allowed_countries": campaign.allowed_countries,
                "allowed_us_states": campaign.allowed_us_states,
            },
            on_conflict="slug",
        ).execute()
        logger.info("skill_2_db_upsert", slug=campaign_slug)
    except Exception as exc:
        logger.warn("skill_2_db_unavailable", error=str(exc))

    return {"slug": campaign_slug, "strategy_path": str(strategy_path)}
