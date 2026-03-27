"""Metrics domain models."""

from __future__ import annotations

from pydantic import BaseModel


class SequenceMetrics(BaseModel):
    """Apollo sequence performance metrics."""

    sent: int = 0
    opened: int = 0
    clicked: int = 0
    replied: int = 0
    bounced: int = 0
    unsubscribed: int = 0

    @property
    def open_rate(self) -> float:
        return self.opened / self.sent if self.sent > 0 else 0.0

    @property
    def reply_rate(self) -> float:
        return self.replied / self.sent if self.sent > 0 else 0.0

    @property
    def bounce_rate(self) -> float:
        return self.bounced / self.sent if self.sent > 0 else 0.0


class CampaignMetrics(BaseModel):
    """Aggregated campaign-level metrics."""

    total_companies: int = 0
    qualified_companies: int = 0
    total_contacts: int = 0
    total_messages: int = 0
    sequences: dict[str, SequenceMetrics] = {}
