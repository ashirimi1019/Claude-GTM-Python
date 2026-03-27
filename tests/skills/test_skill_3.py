"""Tests for Skill 3 — Campaign Copy."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.skills.skill_3_campaign_copy import run_skill_3


@pytest.fixture
def _campaign_dir(tmp_path, monkeypatch):
    """Create a minimal offer + campaign with positioning.md and strategy.md."""
    offer_dir = tmp_path / "test-offer"
    offer_dir.mkdir()
    (offer_dir / "positioning.md").write_text(
        "# Test Offer\n\nPositioning content.", encoding="utf-8"
    )

    campaign_dir = offer_dir / "campaigns" / "test-campaign"
    campaign_dir.mkdir(parents=True)
    (campaign_dir / "strategy.md").write_text(
        "# Campaign Strategy\n\nTarget data engineers.", encoding="utf-8"
    )

    # Point context_dir to a temp location with copywriting files
    context_dir = tmp_path / "context"
    (context_dir / "copywriting").mkdir(parents=True)
    (context_dir / "copywriting" / "email-principles.md").write_text("Be concise.", encoding="utf-8")
    (context_dir / "copywriting" / "linkedin-principles.md").write_text("Be personal.", encoding="utf-8")

    monkeypatch.setenv("CONTEXT_DIR", str(context_dir))
    from app.config import get_settings
    get_settings.cache_clear()

    return tmp_path


MOCK_COPY_RESULT = {
    "email_variants": [
        {"subject": "Data team scaling?", "body": "Hi {{name}}...", "variant_name": "Signal A"},
        {"subject": "Hiring plans?", "body": "Noticed you...", "variant_name": "Signal B"},
    ],
    "linkedin_variants": [
        {"body": "Hey — saw your team is growing...", "variant_name": "Growth"},
    ],
    "personalization_notes": "Reference specific job postings.",
}


class TestSkill3:
    async def test_reads_strategy_and_calls_openai(self, _campaign_dir):
        """Skill 3 reads strategy.md and calls OpenAI generate_copy."""
        with (
            patch(
                "core.skills.skill_3_campaign_copy.generate_copy",
                new_callable=AsyncMock, return_value=MOCK_COPY_RESULT,
            ) as mock_gen,
            patch("core.skills.skill_3_campaign_copy._resolve_vertical_id", return_value=None),
            patch("clients.supabase_client.get_supabase_client") as mock_db,
        ):
            mock_client = MagicMock()
            mock_chain = mock_client.table.return_value.select.return_value.eq.return_value
            mock_chain.maybe_single.return_value.execute.return_value = MagicMock(data={"id": "camp-123"})
            mock_client.table.return_value.upsert.return_value.execute.return_value = None
            mock_client.table.return_value.insert.return_value.execute.return_value = None
            mock_db.return_value = mock_client

            result = await run_skill_3(
                "test-offer", "test-campaign", offers_dir=str(_campaign_dir)
            )

        mock_gen.assert_called_once()
        assert result["variants"]["email"] == 2
        assert result["variants"]["linkedin"] == 1
        assert result["cost_usd"] > 0

    async def test_writes_copy_files(self, _campaign_dir):
        """Skill 3 writes email-variants.md, linkedin-variants.md, personalization-notes.md."""
        with (
            patch(
                "core.skills.skill_3_campaign_copy.generate_copy",
                new_callable=AsyncMock, return_value=MOCK_COPY_RESULT,
            ),
            patch("core.skills.skill_3_campaign_copy._resolve_vertical_id", return_value=None),
            patch("clients.supabase_client.get_supabase_client") as mock_db,
        ):
            mock_client = MagicMock()
            mock_chain = mock_client.table.return_value.select.return_value.eq.return_value
            mock_chain.maybe_single.return_value.execute.return_value = MagicMock(data={"id": "camp-123"})
            mock_client.table.return_value.upsert.return_value.execute.return_value = None
            mock_client.table.return_value.insert.return_value.execute.return_value = None
            mock_db.return_value = mock_client

            await run_skill_3(
                "test-offer", "test-campaign", offers_dir=str(_campaign_dir)
            )

        copy_dir = _campaign_dir / "test-offer" / "campaigns" / "test-campaign" / "copy"
        assert (copy_dir / "email-variants.md").exists()
        assert (copy_dir / "linkedin-variants.md").exists()
        assert (copy_dir / "personalization-notes.md").exists()

        email_content = (copy_dir / "email-variants.md").read_text(encoding="utf-8")
        assert "Signal A" in email_content
        assert "Data team scaling?" in email_content
