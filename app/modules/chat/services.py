"""AI Tutor Chat orchestration for RAG context, tools, and history persistence.

When it runs: Called on every `POST /chat` message and session history query.
How & why: Confirms thread ownership, retrieves `>= 0.70` study chunks, releases
the DB transaction before calling Gemini, locks `user_id` into tools, and saves both turns.
"""

from app.core.constants import DEFAULT_HISTORY_LIMIT, MIN_RAG_SIMILARITY
from app.core.database import release_transaction
from app.core.exceptions import NotFoundError
from app.integrations.llm.chat import chat_with_tools
from app.modules.chat.repositories import ChatRepository
from app.modules.chat.schemas import (
    ChatRequest,
    ChatResponse,
    SessionDetailResponse,
    SessionResponse,
    StoredChatMessageSchema,
    ToolCallRecord,
)
from app.modules.chat.tools import build_chat_tools
from app.modules.materials.services import MaterialService


def _dedupe_titles(chunks: list) -> list[str]:
    """Collect unique study material titles in retrieval order."""
    seen: list[str] = []
    for chunk in chunks:
        if chunk.material_title and chunk.material_title not in seen:
            seen.append(chunk.material_title)
    return seen


class ChatService:
    """Orchestrates chat sessions, pgvector RAG context, Gemini tool calling, and persistence."""

    def __init__(self, chat_repo: ChatRepository, material_service: MaterialService):
        self.chat_repo = chat_repo
        self.material_service = material_service

    async def _resolve_session_id(self, user_id: int, req: ChatRequest) -> int:
        """Reuse an existing session if `user_id` owns it; otherwise create a new thread."""
        if req.session_id:
            owner_id = await self.chat_repo.get_session_owner_id(req.session_id)
            if owner_id == user_id:
                return req.session_id
        title = req.message[:40] if req.message else "Study Session"
        created = await self.chat_repo.create_session(user_id, title)
        return created.id

    async def _build_rag_context(self, query: str) -> tuple[str | None, list[str]]:
        """Retrieve up to 3 relevant study chunks (`similarity >= MIN_RAG_SIMILARITY`) and unique titles."""
        relevant = await self.material_service.search_chunks(query, limit=3, min_similarity=MIN_RAG_SIMILARITY)
        if not relevant:
            return None, []
        blocks = [
            f"[Chunk #{chunk.chunk_index} ({chunk.material_title or 'Study Guide'})]: {chunk.content}"
            for chunk in relevant
        ]
        return "\n---\n".join(blocks), _dedupe_titles(relevant)

    async def chat(self, user_id: int, req: ChatRequest) -> ChatResponse:
        """Handle a tutor chat turn: fetch RAG context, run Gemini + tools, save transcript."""
        session_id = await self._resolve_session_id(user_id, req)
        rag_context, sources = await self._build_rag_context(req.message)
        history = [{"role": h.role, "content": h.content} for h in req.history]

        # End the read transaction before waiting on Gemini so Postgres pool connections stay free.
        await release_transaction(self.chat_repo.session)

        reply, tool_calls_executed = await chat_with_tools(req.message, history, rag_context, build_chat_tools(user_id))
        await self.chat_repo.add_messages(
            session_id,
            [("user", req.message, None), ("assistant", reply, tool_calls_executed)],
        )
        return ChatResponse(
            message=reply,
            session_id=session_id,
            tool_calls=[ToolCallRecord.model_validate(tc) for tc in tool_calls_executed],
            sources=sources,
        )

    async def list_sessions(
        self,
        user_id: int,
        limit: int = DEFAULT_HISTORY_LIMIT,
        offset: int = 0,
    ) -> list[SessionResponse]:
        """List saved chat conversations belonging to the logged-in user."""
        sessions = await self.chat_repo.list_user_sessions(user_id, limit=limit, offset=offset)
        return [SessionResponse.model_validate(session) for session in sessions]

    async def get_session(self, session_id: int, user_id: int) -> SessionDetailResponse:
        """Load one chat thread or raise HTTP 404 if absent or owned by another user."""
        session = await self.chat_repo.get_session(session_id)
        if not session or session.user_id != user_id:
            raise NotFoundError(f"Chat session with id {session_id} not found")

        messages = [StoredChatMessageSchema(role=msg.role, content=msg.content) for msg in session.messages]
        return SessionDetailResponse(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            messages=messages,
        )
