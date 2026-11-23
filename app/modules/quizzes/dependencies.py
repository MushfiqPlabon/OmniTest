"""FastAPI dependency factories for the quizzes module (`QuizRepository` -> `QuizService`)."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.modules.quizzes.repositories import QuizRepository
from app.modules.quizzes.services import QuizService


def get_quiz_repo(session: AsyncSession = Depends(get_db_session)) -> QuizRepository:
    """Provide a per-request `QuizRepository` bound to the active DB session."""
    return QuizRepository(session)


def get_quiz_service(repo: QuizRepository = Depends(get_quiz_repo)) -> QuizService:
    """Provide a `QuizService` instance wired with `QuizRepository`."""
    return QuizService(repo)
