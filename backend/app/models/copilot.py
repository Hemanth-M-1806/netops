"""Copilot / chat Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Role = Literal["user", "assistant", "system"]


class ChatMessageIn(BaseModel):
    session_id: str = Field(min_length=1, max_length=36)
    content: str = Field(min_length=1, max_length=8000)
    # optional: scope the LLM context to a specific device
    device_id: int | None = None
    interface_id: int | None = None


class ChatMessageOut(BaseModel):
    id: int
    session_id: str
    role: Role
    content: str
    token_count: int | None
    created_at: datetime


class ChatResponse(BaseModel):
    """The assistant's reply plus the persisted message record."""
    assistant_message: ChatMessageOut
    # metadata from the RAG retrieval step
    context_metrics_used: int = 0
    context_alerts_used: int = 0
