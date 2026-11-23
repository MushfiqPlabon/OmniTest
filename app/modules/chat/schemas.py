"""Pydantic schemas for AI Tutor Chat requests, responses, tool logs, and transcripts."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageSchema(BaseModel):
    """Single incoming message turn in `ChatRequest.history` (bounded at 8,000 chars)."""

    role: Literal["user", "assistant", "system"]
    content: str = Field(..., max_length=8000)


class StoredChatMessageSchema(BaseModel):
    """Persisted message turn returned from `GET /chat/sessions/{id}` (no truncation cap)."""

    role: str
    content: str


class ChatRequest(BaseModel):
    """Incoming student question with optional recent turns and persistent `session_id`."""

    message: str = Field(..., min_length=1, max_length=4000, description="Student's chat message")
    history: list[ChatMessageSchema] = Field(
        default_factory=list, max_length=40, description="Previous conversation turns for multi-turn chat"
    )
    session_id: int | None = Field(default=None, description="Optional chat session ID for persistence")


class ToolCallRecord(BaseModel):
    """Audit record of a validated DB tool executed during a tutor response."""

    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Any = None


class ChatResponse(BaseModel):
    """Completed tutor response together with session ID, tool logs, and RAG source titles."""

    message: str
    session_id: int
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class SessionResponse(BaseModel):
    """Metadata summary for one saved conversation thread."""

    id: int
    user_id: int
    title: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionDetailResponse(SessionResponse):
    """Full conversation thread including saved messages in chronological order."""

    messages: list[StoredChatMessageSchema] = Field(default_factory=list)
