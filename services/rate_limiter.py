"""Rate limiter — stub that always allows requests (for now)."""

from __future__ import annotations


def check_rate_limit(api_name: str, max_per_hour: int = 100) -> bool:
    """Check if an API call is within rate limits.

    Stub implementation: always returns True.
    Future: integrate with Redis or in-memory sliding window.

    Args:
        api_name: Name of the API being rate-limited (e.g. "apollo", "openai").
        max_per_hour: Maximum calls allowed per hour.

    Returns:
        True if the call is allowed, False if rate-limited.
    """
    return True
