"""FastAPI dependency factories for the AI Tutor Chat module.

Injects `ChatRepository` and `MaterialService` (for RAG search); chat tools open
isolated DB sessions in `app.modules.chat.tools`.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.modules.chat.repositories import ChatRepository
from app.modules.chat.services import ChatService
from app.modules.materials.dependencies import get_material_service
from app.modules.materials.services import MaterialService


def get_chat_repo(session: AsyncSession = Depends(get_db_session)) -> ChatRepository:
    """Create a per-request `ChatRepository` bound to the active DB session."""
    return ChatRepository(session)


def get_chat_service(
    chat_repo: ChatRepository = Depends(get_chat_repo),
    material_service: MaterialService = Depends(get_material_service),
) -> ChatService:
    """Assemble `ChatService` with chat history storage and RAG material search."""
    return ChatService(chat_repo, material_service)
