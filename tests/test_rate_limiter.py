"""Tests for services/rate_limiter.py."""

from services.rate_limiter import check_rate_limit


class TestCheckRateLimit:
    def test_always_returns_true(self):
        assert check_rate_limit("apollo") is True

    def test_with_custom_max(self):
        assert check_rate_limit("openai", max_per_hour=50) is True

    def test_different_api_names(self):
        assert check_rate_limit("apollo") is True
        assert check_rate_limit("openai") is True
        assert check_rate_limit("supabase") is True
