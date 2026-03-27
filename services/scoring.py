"""Legacy scoring service — used when ICP Builder profile is not set.

Parses scoring config from vertical scoring.md YAML blocks and applies
scoring_config_overrides from the database.
"""

from __future__ import annotations

import re
from typing import Any

import yaml

# Default scoring config (used when nothing else is available)
DEFAULT_SCORING_CONFIG: dict[str, Any] = {
    "strictness": "broad",
    "threshold": 75,
    "min_employees": 50,
    "max_employees": 10000,
    "preferred_funding": ["series_a", "series_b", "series_c"],
    "acceptable_funding": ["seed", "series_d_plus", "private_equity"],
    "preferred_tech": [],
    "preferred_industries": [],
    "excluded_industries": [],
    "competitor_detection": True,
}


def parse_scoring_config(scoring_md: str) -> dict[str, Any]:
    """Parse scoring configuration from a vertical's scoring.md file.

    Looks for YAML blocks between ```yaml and ``` markers.

    Args:
        scoring_md: Contents of a vertical scoring.md file.

    Returns:
        Merged scoring config dict.
    """
    config = DEFAULT_SCORING_CONFIG.copy()

    # Find YAML blocks
    yaml_pattern = r"```yaml\s*\n(.*?)```"
    matches = re.findall(yaml_pattern, scoring_md, re.DOTALL)

    for match in matches:
        try:
            parsed = yaml.safe_load(match)
            if isinstance(parsed, dict):
                config.update(parsed)
        except yaml.YAMLError:
            continue

    return config


def resolve_scoring_config(
    offer_overrides: dict[str, Any] | None = None,
    campaign_overrides: dict[str, Any] | None = None,
    vertical_scoring_md: str | None = None,
) -> dict[str, Any]:
    """Resolve the effective scoring config using the cascade:

    campaign_overrides > offer_overrides > parsed vertical scoring.md > DEFAULT

    Args:
        offer_overrides: scoring_config_overrides from offer table.
        campaign_overrides: scoring_config_overrides from campaign table.
        vertical_scoring_md: Contents of the vertical's scoring.md.

    Returns:
        Resolved scoring config dict.
    """
    # Start with defaults
    config = DEFAULT_SCORING_CONFIG.copy()

    # Layer 1: Parse vertical scoring.md
    if vertical_scoring_md:
        parsed = parse_scoring_config(vertical_scoring_md)
        config.update(parsed)

    # Layer 2: Offer overrides
    if offer_overrides:
        config.update(offer_overrides)

    # Layer 3: Campaign overrides (highest priority)
    if campaign_overrides:
        config.update(campaign_overrides)

    return config
