"""HTTP endpoints for AI Tutor Chat (`/api/v1/chat`).

When it runs: On chat turns (`POST /chat`) and session history lookups (`GET`).
How & why: Validates chat messages and turn history with Pydantic, verifies
authentication with `get_current_user`, and passes `current_user.id` directly
so callers cannot impersonate another user's chat threads.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.constants import DEFAULT_HISTORY_LIMIT, MAX_HISTORY_LIMIT
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.chat.dependencies import get_chat_service
from app.modules.chat.schemas import ChatRequest, ChatResponse, SessionDetailResponse, SessionResponse
from app.modules.chat.services import ChatService

router = APIRouter(prefix="/chat", tags=["AI Tutor Chat & RAG"])


@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    payload: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatResponse:
    """Multi-turn AI tutor chat with pgvector RAG retrieval and database tool calling."""
    return await service.chat(current_user.id, payload)


@router.get("/sessions", response_model=list[SessionResponse], status_code=status.HTTP_200_OK)
async def list_chat_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ChatService, Depends(get_chat_service)],
    limit: Annotated[int, Query(ge=1, le=MAX_HISTORY_LIMIT)] = DEFAULT_HISTORY_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[SessionResponse]:
    """List saved chat sessions belonging strictly to the logged-in user."""
    return await service.list_sessions(current_user.id, limit=limit, offset=offset)


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse, status_code=status.HTTP_200_OK)
async def get_chat_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> SessionDetailResponse:
    """Fetch a single chat session and its full message transcript (owner-only)."""
    return await service.get_session(session_id, current_user.id)
