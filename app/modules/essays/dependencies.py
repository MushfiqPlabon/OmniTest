"""FastAPI dependency factories for the essay prompts & AI grading module."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.modules.essays.repositories import EssayRepository
from app.modules.essays.services import EssayService


def get_essay_repo(session: AsyncSession = Depends(get_db_session)) -> EssayRepository:
    """Create a per-request `EssayRepository` using the active database session."""
    return EssayRepository(session)


def get_essay_service(repo: EssayRepository = Depends(get_essay_repo)) -> EssayService:
    """Create a per-request `EssayService` backed by `EssayRepository`."""
    return EssayService(repo)
