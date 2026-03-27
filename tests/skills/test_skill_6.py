"""Tests for Skill 6 — Campaign Review."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_METRICS = [
    {
        "sequence_id": "seq-1",
        "name": "test-offer__test-campaign__decision_maker",
        "active": True,
        "sent": 100,
        "opened": 35,
        "clicked": 5,
        "replied": 4,
        "bounced": 2,
        "unsubscribed": 1,
        "total_contacts": 100,
    },
    {
        "sequence_id": "seq-2",
        "name": "test-offer__test-campaign__influencer",
        "active": True,
        "sent": 50,
        "opened": 10,
        "clicked": 1,
        "replied": 1,
        "bounced": 1,
        "unsubscribed": 0,
        "total_contacts": 50,
    },
]


# ---------------------------------------------------------------------------
# Test 1: Generates learnings.md
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generates_learnings(tmp_path: Path):
    """Skill 6 should write a learnings.md file with metrics analysis."""
    from core.skills.skill_6_campaign_review import run_skill_6

    async def mock_load_sequences(offer_slug, campaign_slug):
        return [
            {"apollo_sequence_id": "seq-1"},
            {"apollo_sequence_id": "seq-2"},
        ]

    with patch(
        "core.skills.skill_6_campaign_review.get_sequence_analytics",
        new_callable=AsyncMock,
        side_effect=lambda seq_id, **kw: next(
            m for m in SAMPLE_METRICS if m["sequence_id"] == seq_id
        ),
    ):
        result = await run_skill_6(
            offer_slug="test-offer",
            campaign_slug="test-campaign",
            offers_dir=str(tmp_path),
            apollo_api_key="fake-key",
            db_load_sequences=mock_load_sequences,
            context_dir=str(tmp_path / "context"),
        )

    assert result["sequences_analyzed"] == 2
    assert result["learnings_written"] is True

    learnings_path = (
        tmp_path / "test-offer" / "campaigns" / "test-campaign" / "results" / "learnings.md"
    )
    assert learnings_path.exists()

    content = learnings_path.read_text(encoding="utf-8")
    assert "Campaign Review" in content
    assert "Open rate" in content
    assert "Reply rate" in content
    assert "Bounce rate" in content


# ---------------------------------------------------------------------------
# Test 2: Updates what-works.md
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_updates_what_works(tmp_path: Path):
    """Skill 6 should append campaign learnings to what-works.md."""
    from core.skills.skill_6_campaign_review import run_skill_6

    # Pre-create a what-works.md with existing content
    context_dir = tmp_path / "context"
    learnings_dir = context_dir / "learnings"
    learnings_dir.mkdir(parents=True, exist_ok=True)
    what_works = learnings_dir / "what-works.md"
    what_works.write_text("# What Works\n\nExisting content.\n", encoding="utf-8")

    async def mock_load_sequences(offer_slug, campaign_slug):
        return [{"apollo_sequence_id": "seq-1"}]

    with patch(
        "core.skills.skill_6_campaign_review.get_sequence_analytics",
        new_callable=AsyncMock,
        return_value=SAMPLE_METRICS[0],
    ):
        result = await run_skill_6(
            offer_slug="test-offer",
            campaign_slug="test-campaign",
            offers_dir=str(tmp_path),
            apollo_api_key="fake-key",
            db_load_sequences=mock_load_sequences,
            context_dir=str(context_dir),
        )

    assert result["learnings_written"] is True

    content = what_works.read_text(encoding="utf-8")
    assert "Existing content." in content, "Must preserve existing content"
    assert "test-offer / test-campaign" in content, "Must append new campaign entry"
    assert "Open rate:" in content
    assert "Reply rate:" in content
