"""Tests for Skill 1 — New Offer."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from core.skills.skill_1_new_offer import run_skill_1


@pytest.fixture
def offer_config():
    return {
        "name": "Talent as a Service (US)",
        "description": "Staff augmentation for US tech companies",
        "vertical_id": "staffing",
        "allowed_countries": ["US", "CA"],
        "allowed_us_states": ["CA", "NY"],
    }


class TestSkill1:
    async def test_creates_dir_and_positioning(self, tmp_path, offer_config):
        """Skill 1 creates the offer directory and writes positioning.md."""
        with patch("clients.supabase_client.get_supabase_client") as mock_db:
            mock_client = MagicMock()
            mock_client.table.return_value.upsert.return_value.execute.return_value = None
            mock_db.return_value = mock_client

            result = await run_skill_1(offer_config, offers_dir=str(tmp_path))

        positioning_path = Path(result["positioning_path"])
        assert positioning_path.exists()
        content = positioning_path.read_text(encoding="utf-8")
        assert "Talent as a Service (US)" in content
        assert "Staff augmentation" in content
        assert "US, CA" in content

    async def test_generates_slug(self, tmp_path, offer_config):
        """Skill 1 generates a URL-safe slug from the offer name."""
        with patch("clients.supabase_client.get_supabase_client") as mock_db:
            mock_client = MagicMock()
            mock_client.table.return_value.upsert.return_value.execute.return_value = None
            mock_db.return_value = mock_client

            result = await run_skill_1(offer_config, offers_dir=str(tmp_path))

        assert result["slug"] == "talent-as-a-service-us"
        assert (tmp_path / "talent-as-a-service-us").is_dir()

    async def test_handles_missing_vertical(self, tmp_path):
        """Skill 1 works without vertical_id (no vertical context appended)."""
        config = {
            "name": "Generic Offer",
            "description": "A test offer",
        }
        with patch("clients.supabase_client.get_supabase_client") as mock_db:
            mock_client = MagicMock()
            mock_client.table.return_value.upsert.return_value.execute.return_value = None
            mock_db.return_value = mock_client

            result = await run_skill_1(config, offers_dir=str(tmp_path))

        assert result["slug"] == "generic-offer"
        content = Path(result["positioning_path"]).read_text(encoding="utf-8")
        assert "Generic Offer" in content
        assert "Vertical Context" not in content
