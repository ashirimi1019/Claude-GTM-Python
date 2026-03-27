"""Apollo client shared utilities — domain normalization, headers, retry."""

from __future__ import annotations

import re
from urllib.parse import urlparse


def normalize_domain(domain: str) -> str:
    """Normalize a domain: lowercase, strip protocol/www/path.

    Examples:
        "https://www.acme.com/about" → "acme.com"
        "Acme.COM" → "acme.com"
        "www.acme.com" → "acme.com"
    """
    domain = domain.lower().strip()

    # Strip protocol
    if "://" in domain:
        parsed = urlparse(domain)
        domain = parsed.netloc or parsed.path

    # Strip www prefix
    if domain.startswith("www."):
        domain = domain[4:]

    # Strip trailing path/slash
    domain = domain.split("/")[0]

    return domain


def api_headers(api_key: str) -> dict[str, str]:
    """Standard Apollo API request headers."""
    return {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": api_key,
    }


APOLLO_BASE_URL = "https://api.apollo.io"
