"""Skill 1 — New Offer: generates positioning.md and upserts to Supabase."""

from __future__ import annotations

from pathlib import Path

import structlog

from app.config import get_settings
from models.offer import OfferCreate, slugify
from services.verticals.context_builder import build_skill_context

logger = structlog.get_logger()


async def run_skill_1(config: dict, offers_dir: str = "offers") -> dict:
    """Create a new offer with positioning document.

    Args:
        config: Dict with keys: name, description, vertical_id,
                allowed_countries, allowed_us_states.
        offers_dir: Base directory for offer output files.

    Returns:
        {"slug": str, "positioning_path": str}
    """
    offer = OfferCreate(
        name=config["name"],
        description=config.get("description", ""),
        vertical_id=config.get("vertical_id") or None,
        allowed_countries=config.get("allowed_countries"),
        allowed_us_states=config.get("allowed_us_states"),
    )
    slug = offer.slug
    logger.info("skill_1_start", slug=slug, vertical_id=offer.vertical_id)

    # Build output directory
    offer_dir = Path(offers_dir) / slug
    offer_dir.mkdir(parents=True, exist_ok=True)

    # Assemble positioning content
    positioning_parts: list[str] = [
        f"# {config['name']}\n",
        f"## Description\n\n{offer.description}\n" if offer.description else "",
    ]

    # Add vertical context if available
    if offer.vertical_id:
        settings = get_settings()
        vertical_context = build_skill_context(
            skill_id=1,
            vertical_slug=offer.vertical_id,
            base_dir=str(Path(settings.context_dir) / "verticals"),
        )
        if vertical_context:
            positioning_parts.append(f"\n## Vertical Context\n\n{vertical_context}\n")

    if offer.allowed_countries:
        positioning_parts.append(
            f"\n## Target Geography\n\nCountries: {', '.join(offer.allowed_countries)}\n"
        )
    if offer.allowed_us_states:
        positioning_parts.append(f"US States: {', '.join(offer.allowed_us_states)}\n")

    positioning_md = "\n".join(part for part in positioning_parts if part)
    positioning_path = offer_dir / "positioning.md"
    positioning_path.write_text(positioning_md, encoding="utf-8")
    logger.info("skill_1_positioning_written", path=str(positioning_path))

    # Upsert to Supabase (graceful degradation)
    try:
        from clients.supabase_client import get_supabase_client

        db = get_supabase_client()
        db.table("offers").upsert(
            {
                "slug": slug,
                "name": config["name"],
                "description": offer.description,
                "default_vertical_id": offer.vertical_id,
                "status": "draft",
                "allowed_countries": offer.allowed_countries,
                "allowed_us_states": offer.allowed_us_states,
            },
            on_conflict="slug",
        ).execute()
        logger.info("skill_1_db_upsert", slug=slug)
    except Exception as exc:
        logger.warn("skill_1_db_unavailable", error=str(exc))

    return {"slug": slug, "positioning_path": str(positioning_path)}
