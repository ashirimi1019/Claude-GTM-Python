"""Message and MessageVariant domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


ChannelType = Literal["email", "linkedin", "sms"]
MessageStatus = Literal[
    "draft", "scheduled", "sent", "bounced", "opened", "clicked", "replied", "opted_out"
]


class Message(BaseModel):
    """A sent message — maps to the `messages` table."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = ""
    campaign_id: str = ""
    contact_id: str = ""
    company_id: str = ""
    message_variant_id: str | None = None
    channel: ChannelType = "email"
    subject: str | None = None
    body: str = ""
    status: MessageStatus = "draft"
    sent_at: datetime | None = None
    opened_at: datetime | None = None
    clicked_at: datetime | None = None
    replied_at: datetime | None = None
    bounce_reason: str | None = None
    apollo_sequence_id: str | None = None
    apollo_message_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MessageVariant(BaseModel):
    """Email/LinkedIn copy variant — maps to the `message_variants` table."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = ""
    campaign_id: str = ""
    channel: ChannelType = "email"
    subject: str | None = None
    body: str = ""
    personalization_notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
