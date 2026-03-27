"""Tests for Skill 2 — Campaign Strategy."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.skills.skill_2_campaign_strategy import run_skill_2


@pytest.fixture
def _offer_dir(tmp_path):
    """Create a minimal offer with positioning.md."""
    offer_dir = tmp_path / "test-offer"
    offer_dir.mkdir()
    (offer_dir / "positioning.md").write_text(
        "# Test Offer\n\nSome positioning content.", encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def campaign_config():
    return {
        "offer_slug": "test-offer",
        "name": "Hiring Data Engineers",
        "vertical_id": "staffing",
        "allowed_countries": ["US"],
        "allowed_us_states": None,
    }


class TestSkill2:
    async def test_creates_strategy_md(self, _offer_dir, campaign_config):
        """Skill 2 creates strategy.md in the campaign directory."""
        with patch("core.skills.skill_2_campaign_strategy.get_supabase_client") as mock_db:
            mock_client = MagicMock()
            mock_chain = mock_client.table.return_value.select.return_value.eq.return_value
            mock_chain.maybe_single.return_value.execute.return_value = MagicMock(data={"id": "offer-123"})
            mock_client.table.return_value.upsert.return_value.execute.return_value = None
            mock_db.return_value = mock_client

            result = await run_skill_2(campaign_config, offers_dir=str(_offer_dir))

        strategy_path = Path(result["strategy_path"])
        assert strategy_path.exists()
        content = strategy_path.read_text(encoding="utf-8")
        assert "Hiring Data Engineers" in content
        assert "Some positioning content" in content

    async def test_validates_offer_exists(self, tmp_path, campaign_config):
        """Skill 2 raises FileNotFoundError if offer positioning.md is missing."""
        with pytest.raises(FileNotFoundError, match="positioning"):
            await run_skill_2(campaign_config, offers_dir=str(tmp_path))

    async def test_generates_slug(self, _offer_dir, campaign_config):
        """Skill 2 generates a URL-safe slug from the campaign name."""
        with patch("core.skills.skill_2_campaign_strategy.get_supabase_client") as mock_db:
            mock_client = MagicMock()
            mock_chain = mock_client.table.return_value.select.return_value.eq.return_value
            mock_chain.maybe_single.return_value.execute.return_value = MagicMock(data={"id": "offer-123"})
            mock_client.table.return_value.upsert.return_value.execute.return_value = None
            mock_db.return_value = mock_client

            result = await run_skill_2(campaign_config, offers_dir=str(_offer_dir))

        assert result["slug"] == "hiring-data-engineers"
