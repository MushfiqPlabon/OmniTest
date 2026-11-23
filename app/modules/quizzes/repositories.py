"""Async database queries for quizzes, questions, and student quiz attempts.

Why `selectinload` is used here:
Async SQLAlchemy cannot lazily load `quiz.questions` outside an open query,
so `selectinload(...)` fetches related rows in a single batched SELECT.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.constants import DEFAULT_HISTORY_LIMIT
from app.core.repository import BaseRepository
from app.modules.quizzes.models import Quiz, QuizAttempt


class QuizRepository(BaseRepository):
    """Inherits quiz CRUD from `BaseRepository` and loads nested questions/attempts."""

    model = Quiz

    async def create(self, entity: Quiz) -> Quiz:
        """Persist a new quiz plus nested questions and refresh child rows."""
        saved = await super().create(entity)
        await self.session.refresh(saved, ["questions"])
        return saved

    async def get_by_id(self, entity_id: int, options: Sequence[Any] = ()) -> Quiz | None:
        """Load one quiz together with its `questions` relationship pre-populated."""
        load_options = options or (selectinload(Quiz.questions),)
        return await super().get_by_id(entity_id, options=load_options)

    async def create_attempt(self, attempt: QuizAttempt) -> QuizAttempt:
        """Insert a graded quiz attempt and reload database timestamps."""
        self.session.add(attempt)
        await self.session.commit()
        await self.session.refresh(attempt)
        return attempt

    async def get_attempts(
        self,
        quiz_id: int | None = None,
        user_id: int | None = None,
        subject: str | None = None,
        limit: int = DEFAULT_HISTORY_LIMIT,
        offset: int = 0,
    ) -> list[QuizAttempt]:
        """List quiz attempts filtered by quiz, user, and/or subject, newest first."""
        stmt = select(QuizAttempt).options(selectinload(QuizAttempt.quiz))
        if subject is not None:
            stmt = stmt.join(QuizAttempt.quiz).where(Quiz.subject == subject.strip().lower())
        if quiz_id is not None:
            stmt = stmt.where(QuizAttempt.quiz_id == quiz_id)
        if user_id is not None:
            stmt = stmt.where(QuizAttempt.user_id == user_id)
        stmt = stmt.order_by(QuizAttempt.completed_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
