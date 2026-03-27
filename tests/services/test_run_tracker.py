"""Tests for SkillRunTracker with mocked Redis."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from services.run_tracker import SkillRunTracker


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    with patch("services.run_tracker.redis.from_url") as mock_from_url:
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        yield mock_client


@pytest.fixture
def tracker(mock_redis):
    """Create a SkillRunTracker with mocked Redis."""
    return SkillRunTracker(
        skill_id=1,
        offer_slug="test-offer",
        campaign_slug="test-campaign",
        redis_url="redis://localhost:6379/0",
    )


@pytest.fixture
def tracker_no_campaign(mock_redis):
    """Create a SkillRunTracker without a campaign slug."""
    return SkillRunTracker(
        skill_id=3,
        offer_slug="test-offer",
        campaign_slug=None,
        redis_url="redis://localhost:6379/0",
    )


class TestSkillRunTrackerInit:
    """Tests for tracker initialization."""

    def test_channel_format(self, tracker):
        assert tracker.channel == "skill-run:test-offer:test-campaign:1"

    def test_channel_format_no_campaign(self, tracker_no_campaign):
        assert tracker_no_campaign.channel == "skill-run:test-offer:none:3"

    def test_initial_steps_empty(self, tracker):
        assert tracker.steps == []

    def test_attributes_set(self, tracker):
        assert tracker.skill_id == 1
        assert tracker.offer_slug == "test-offer"
        assert tracker.campaign_slug == "test-campaign"


class TestSkillRunTrackerLog:
    """Tests for the log() method."""

    def test_log_publishes_to_redis(self, tracker, mock_redis):
        tracker.log("Starting skill execution")

        mock_redis.publish.assert_called_once()
        channel, data = mock_redis.publish.call_args[0]
        assert channel == "skill-run:test-offer:test-campaign:1"

        parsed = json.loads(data)
        assert parsed["level"] == "info"
        assert parsed["message"] == "Starting skill execution"
        assert "ts" in parsed

    def test_log_custom_level(self, tracker, mock_redis):
        tracker.log("Something went wrong", level="error")

        _, data = mock_redis.publish.call_args[0]
        parsed = json.loads(data)
        assert parsed["level"] == "error"

    def test_log_appends_to_steps(self, tracker, mock_redis):
        tracker.log("Step 1")
        tracker.log("Step 2")
        assert len(tracker.steps) == 2
        assert tracker.steps[0]["message"] == "Step 1"
        assert tracker.steps[1]["message"] == "Step 2"

    def test_log_survives_redis_failure(self, tracker, mock_redis):
        import redis as redis_lib

        mock_redis.publish.side_effect = redis_lib.RedisError("Connection refused")
        # Should not raise
        tracker.log("This should not fail")
        assert len(tracker.steps) == 1


class TestSkillRunTrackerSteps:
    """Tests for start_step, complete_step, fail_step."""

    def test_start_step(self, tracker, mock_redis):
        tracker.start_step("enrichment")

        _, data = mock_redis.publish.call_args[0]
        parsed = json.loads(data)
        assert parsed["step"] == "enrichment"
        assert parsed["step_status"] == "started"
        assert "Step started: enrichment" in parsed["message"]

    def test_complete_step(self, tracker, mock_redis):
        tracker.complete_step("enrichment")

        _, data = mock_redis.publish.call_args[0]
        parsed = json.loads(data)
        assert parsed["step"] == "enrichment"
        assert parsed["step_status"] == "completed"

    def test_fail_step(self, tracker, mock_redis):
        tracker.fail_step("enrichment", "API timeout")

        _, data = mock_redis.publish.call_args[0]
        parsed = json.loads(data)
        assert parsed["step"] == "enrichment"
        assert parsed["step_status"] == "failed"
        assert parsed["error"] == "API timeout"
        assert parsed["level"] == "error"

    def test_full_step_lifecycle(self, tracker, mock_redis):
        tracker.start_step("scoring")
        tracker.log("Processing 50 companies")
        tracker.complete_step("scoring")

        assert len(tracker.steps) == 3
        assert tracker.steps[0]["step_status"] == "started"
        assert tracker.steps[1]["message"] == "Processing 50 companies"
        assert tracker.steps[2]["step_status"] == "completed"
