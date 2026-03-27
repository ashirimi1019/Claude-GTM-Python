"""Tests for Skill 5 — Launch Outreach."""

from __future__ import annotations

import csv
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# ---------------------------------------------------------------------------
# Test 1: Groups contacts by segment
# ---------------------------------------------------------------------------

def test_group_contacts_by_segment():
    """Contacts should be grouped into decision_maker, influencer, implementer, other."""
    from core.skills.skill_5_launch_outreach import group_contacts_by_segment

    contacts = [
        {"email": "cto@acme.com", "segment": "decision_maker"},
        {"email": "vp@acme.com", "segment": "decision_maker"},
        {"email": "mgr@acme.com", "segment": "influencer"},
        {"email": "dev@acme.com", "segment": "implementer"},
        {"email": "intern@acme.com", "segment": "other"},
        {"email": "unknown@acme.com"},  # missing segment -> "other"
    ]

    groups = group_contacts_by_segment(contacts)

    assert len(groups["decision_maker"]) == 2
    assert len(groups["influencer"]) == 1
    assert len(groups["implementer"]) == 1
    assert len(groups["other"]) == 2  # "other" + missing segment


# ---------------------------------------------------------------------------
# Test 2: Creates sequences per segment
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_creates_sequences_per_segment(tmp_path: Path):
    """Skill 5 should create one Apollo sequence per non-empty segment."""
    # Set up contacts CSV
    campaign_dir = tmp_path / "test-offer" / "campaigns" / "test-campaign"
    leads_dir = campaign_dir / "leads"
    leads_dir.mkdir(parents=True, exist_ok=True)

    contacts_csv = leads_dir / "contacts.csv"
    with open(contacts_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "email", "company_name", "segment"])
        writer.writeheader()
        writer.writerow({"id": "c1", "email": "cto@acme.com", "company_name": "Acme", "segment": "decision_maker"})
        writer.writerow({"id": "c2", "email": "mgr@acme.com", "company_name": "Acme", "segment": "influencer"})

    # Set up copy variants
    copy_dir = campaign_dir / "copy"
    copy_dir.mkdir(parents=True, exist_ok=True)
    (copy_dir / "email-variants.md").write_text(
        "## Subject: Hello\nBody of email 1\n\n## Subject: Follow up\nBody of email 2\n",
        encoding="utf-8",
    )

    created_sequences: list[str] = []

    async def mock_create_seq(name: str, **kw):
        created_sequences.append(name)
        return {"id": f"seq-{len(created_sequences)}", "name": name}

    with (
        patch("core.skills.skill_5_launch_outreach.create_sequence", side_effect=mock_create_seq),
        patch("core.skills.skill_5_launch_outreach.add_email_step", new_callable=AsyncMock),
        patch("core.skills.skill_5_launch_outreach.activate_sequence", new_callable=AsyncMock),
        patch(
            "core.skills.skill_5_launch_outreach.enroll_sequence",
            new_callable=AsyncMock, return_value={"enrolled": 1, "failed": 0},
        ),
        patch(
            "core.skills.skill_5_launch_outreach.get_email_accounts",
            new_callable=AsyncMock, return_value=[{"id": "acct-1"}],
        ),
    ):
        from core.skills.skill_5_launch_outreach import run_skill_5

        result = await run_skill_5(
            offer_slug="test-offer",
            campaign_slug="test-campaign",
            offers_dir=str(tmp_path),
            apollo_api_key="fake-key",
        )

    # Two non-empty segments: decision_maker and influencer
    assert result["sequences_created"] == 2
    assert len(created_sequences) == 2

    # messages.csv should exist
    messages_csv = campaign_dir / "outreach" / "messages.csv"
    assert messages_csv.exists()
