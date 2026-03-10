from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Qualification(str, Enum):
    QUALIFIED = "qualified"
    NOT_QUALIFIED = "not_qualified"


class HandoffStatus(str, Enum):
    NONE = "none"
    PENDING_HUMAN = "pending_human"
    CLAIMED = "claimed"
    CLOSED = "closed"


class LeadState(BaseModel):
    client_id: str
    source: str = "telegram"
    telegram_user_id: int
    telegram_chat_id: int
    language: str = "ru"
    intent: str | None = None
    timeline: str | None = None
    budget: str | None = None
    contact: str | None = None
    score: int = 0
    warmth: str = "cold"
    qualification: Qualification = Qualification.NOT_QUALIFIED
    risk_flags: list[str] = Field(default_factory=list)
    handoff_status: HandoffStatus = HandoffStatus.NONE
    summary: str | None = None
    transcript: list[dict[str, Any]] = Field(default_factory=list)


class HandoffPayload(BaseModel):
    title: str
    lead_id: str
    score: int
    warmth: str
    qualification: str
    risk_flags: list[str]
    summary: str
    fields: dict[str, str | None]
