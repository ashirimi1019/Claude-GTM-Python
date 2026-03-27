"""Shared test fixtures."""

import os
import pytest


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch):
    """Set minimal env vars so Settings() doesn't fail during tests."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
    monkeypatch.setenv("APOLLO_API_KEY", "test-apollo-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("AGENT_INTERNAL_SECRET", "test-agent-secret")

    # Clear cached settings between tests
    from app.config import get_settings
    get_settings.cache_clear()
