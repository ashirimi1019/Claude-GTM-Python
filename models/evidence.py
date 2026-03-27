"""Evidence (hiring signals) domain model."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

SignalType = Literal[
    "job_posting", "skill_increase", "recent_funding",
    "growth_metrics", "bombora_intent", "other"
]
SignalSource = Literal["apollo", "bombora", "crunchbase", "ats_scrape", "manual"]


class Evidence(BaseModel):
    """A hiring signal for a company — maps to the `evidence` table."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = ""
    company_id: str = ""
    signal_type: SignalType = "other"
    signal_name: str = ""
    intensity: float = 0.0  # 0-100
    recency: float = 0.0  # days since detected
    source: SignalSource = "apollo"
    details: dict[str, Any] | None = None
    created_at: datetime | None = None
    detected_at: datetime | None = None
