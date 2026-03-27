"""Verticals system tests — loader, resolver, context builder."""

from pathlib import Path

import pytest

from app.errors import AppError
from services.verticals.context_builder import build_skill_context
from services.verticals.loader import load_vertical_playbook
from services.verticals.resolver import get_effective_vertical
from services.verticals.types import PLAYBOOK_FILES, SKILL_PLAYBOOK_MAP, VerticalPlaybook

# Real context/verticals dir in the repo
VERTICALS_DIR = str(Path(__file__).resolve().parents[2] / "context" / "verticals")


class TestVerticalPlaybookType:
    def test_has_eight_fields(self):
        assert len(PLAYBOOK_FILES) == 8

    def test_playbook_files_match_dataclass(self):
        """Every key in PLAYBOOK_FILES must be a field on VerticalPlaybook."""
        fields = {f.name for f in VerticalPlaybook.__dataclass_fields__.values()}
        for key in PLAYBOOK_FILES:
            assert key in fields


class TestSkillPlaybookMap:
    def test_all_six_skills(self):
        assert set(SKILL_PLAYBOOK_MAP.keys()) == {1, 2, 3, 4, 5, 6}

    def test_all_keys_valid(self):
        valid = set(PLAYBOOK_FILES.keys())
        for skill_id, keys in SKILL_PLAYBOOK_MAP.items():
            for k in keys:
                assert k in valid, f"Skill {skill_id} references invalid key '{k}'"


class TestLoader:
    def test_loads_staffing(self):
        playbook = load_vertical_playbook("staffing", base_dir=VERTICALS_DIR)
        assert isinstance(playbook, VerticalPlaybook)

    def test_staffing_all_fields_nonempty(self):
        playbook = load_vertical_playbook("staffing", base_dir=VERTICALS_DIR)
        for field in PLAYBOOK_FILES:
            value = getattr(playbook, field)
            assert value, f"Field '{field}' is empty for staffing vertical"

    def test_loads_ai_data_consulting(self):
        playbook = load_vertical_playbook("ai-data-consulting", base_dir=VERTICALS_DIR)
        assert playbook.overview  # at least overview is non-empty

    def test_loads_cloud_software_delivery(self):
        playbook = load_vertical_playbook("cloud-software-delivery", base_dir=VERTICALS_DIR)
        assert playbook.overview

    def test_missing_vertical_returns_empty_fields(self):
        playbook = load_vertical_playbook("nonexistent-vertical", base_dir=VERTICALS_DIR)
        for field in PLAYBOOK_FILES:
            assert getattr(playbook, field) == ""

    def test_caches_results(self):
        """Calling twice with the same args returns the same object (lru_cache)."""
        # Clear cache first to ensure clean state
        load_vertical_playbook.cache_clear()
        a = load_vertical_playbook("staffing", base_dir=VERTICALS_DIR)
        b = load_vertical_playbook("staffing", base_dir=VERTICALS_DIR)
        assert a is b


class TestResolver:
    def test_campaign_overrides_offer(self):
        result = get_effective_vertical("ai-data-consulting", "staffing")
        assert result == "ai-data-consulting"

    def test_falls_back_to_offer(self):
        result = get_effective_vertical(None, "staffing")
        assert result == "staffing"

    def test_campaign_none_falls_back(self):
        result = get_effective_vertical(None, "cloud-software-delivery")
        assert result == "cloud-software-delivery"

    def test_empty_string_campaign_falls_back(self):
        """Empty string is falsy — should fall back to offer."""
        result = get_effective_vertical("", "staffing")
        assert result == "staffing"

    def test_raises_when_both_none(self):
        with pytest.raises(AppError) as exc_info:
            get_effective_vertical(None, None)
        assert exc_info.value.status_code == 422
        assert exc_info.value.code == "MISSING_VERTICAL"

    def test_raises_when_both_empty(self):
        with pytest.raises(AppError):
            get_effective_vertical("", "")


class TestContextBuilder:
    def test_skill_1_includes_overview_icp_buyers(self):
        ctx = build_skill_context(1, "staffing", base_dir=VERTICALS_DIR)
        assert "## Overview" in ctx
        assert "## Icp" in ctx
        assert "## Buyers" in ctx

    def test_skill_1_excludes_scoring(self):
        ctx = build_skill_context(1, "staffing", base_dir=VERTICALS_DIR)
        assert "## Scoring" not in ctx

    def test_skill_4_includes_icp_scoring_signals(self):
        ctx = build_skill_context(4, "staffing", base_dir=VERTICALS_DIR)
        assert "## Icp" in ctx
        assert "## Scoring" in ctx
        assert "## Signals" in ctx

    def test_skill_3_includes_messaging_objections_proof_points(self):
        ctx = build_skill_context(3, "staffing", base_dir=VERTICALS_DIR)
        assert "## Messaging" in ctx
        assert "## Objections" in ctx
        assert "## Proof Points" in ctx

    def test_returns_nonempty_string(self):
        ctx = build_skill_context(1, "staffing", base_dir=VERTICALS_DIR)
        assert len(ctx) > 100  # should be substantial

    def test_unknown_skill_returns_empty(self):
        ctx = build_skill_context(99, "staffing", base_dir=VERTICALS_DIR)
        assert ctx == ""

    def test_sections_separated_by_dividers(self):
        ctx = build_skill_context(2, "staffing", base_dir=VERTICALS_DIR)
        assert "---" in ctx
