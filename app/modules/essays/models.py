"""SQLAlchemy ORM tables for essay writing prompts (`essay_prompts`) and student submissions (`essays`)."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utc_now
from app.modules.auth.models import User


class EssayPrompt(Base):
    """Essay question with its structured JSON grading rubric (criteria + max score)."""

    __tablename__ = "essay_prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    rubric: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey(User.id, ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    essays: Mapped[list["Essay"]] = relationship(
        "Essay",
        back_populates="prompt",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Essay(Base):
    """Student's written essay along with its AI score, rubric breakdown, and feedback."""

    __tablename__ = "essays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id, ondelete="CASCADE"), nullable=False, index=True)
    prompt_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("essay_prompts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_score: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    criteria_scores: Mapped[dict[str, float] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    prompt: Mapped[EssayPrompt] = relationship("EssayPrompt", back_populates="essays")
