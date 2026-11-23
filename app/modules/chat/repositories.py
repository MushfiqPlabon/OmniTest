"""Async database queries for chat sessions and persistent message history."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import DEFAULT_HISTORY_LIMIT
from app.modules.chat.models import ChatMessage, ChatSession


class ChatRepository:
    """Handles chat session creation, ownership lookups, and batched message inserts."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, user_id: int, title: str) -> ChatSession:
        """Create and persist a new conversation thread for `user_id`."""
        chat_sess = ChatSession(user_id=user_id, title=title)
        self.session.add(chat_sess)
        await self.session.commit()
        await self.session.refresh(chat_sess)
        return chat_sess

    async def get_session_owner_id(self, session_id: int) -> int | None:
        """Fetch only the owner `user_id` column for fast ownership verification."""
        stmt = select(ChatSession.user_id).where(ChatSession.id == session_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_session(self, session_id: int) -> ChatSession | None:
        """Load one chat session with all of its messages eagerly loaded."""
        stmt = select(ChatSession).where(ChatSession.id == session_id).options(selectinload(ChatSession.messages))
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def list_user_sessions(
        self,
        user_id: int,
        limit: int = DEFAULT_HISTORY_LIMIT,
        offset: int = 0,
    ) -> list[ChatSession]:
        """Return chat sessions belonging to a user, newest first."""
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def add_messages(
        self,
        session_id: int,
        items: list[tuple[str, str, list[dict[str, Any]] | None]],
    ) -> None:
        """Persist user and assistant messages together in a single database commit."""
        msgs = [
            ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                tool_calls=tool_calls,
            )
            for role, content, tool_calls in items
        ]
        self.session.add_all(msgs)
        await self.session.commit()
