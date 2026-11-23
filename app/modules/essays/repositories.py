"""Database queries for essay prompts (`BaseRepository` CRUD) and student submissions."""

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.constants import DEFAULT_HISTORY_LIMIT
from app.core.repository import BaseRepository
from app.modules.essays.models import Essay, EssayPrompt


class EssayRepository(BaseRepository):
    """Handles CRUD for `EssayPrompt` (inherited) plus saving/listing student `Essay` rows."""

    model = EssayPrompt

    async def create_essay(self, essay: Essay) -> Essay:
        """Persist a newly graded student essay and reload database defaults."""
        self.session.add(essay)
        await self.session.commit()
        await self.session.refresh(essay)
        return essay

    async def get_user_essays(
        self,
        user_id: int,
        subject: str | None = None,
        limit: int = DEFAULT_HISTORY_LIMIT,
        offset: int = 0,
    ) -> list[Essay]:
        """Return one student's essay submissions, optionally filtered by subject, newest first."""
        stmt = select(Essay).options(selectinload(Essay.prompt)).where(Essay.user_id == user_id)
        if subject is not None:
            stmt = stmt.join(Essay.prompt).where(EssayPrompt.subject == subject.strip().lower())
        stmt = stmt.order_by(Essay.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
