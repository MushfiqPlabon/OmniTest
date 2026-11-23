"""Idiomatic fastapi-filter definitions for list endpoints.

Why this exists:
Maps query parameters (`?subject=...&topic=...&difficulty=...&search=...`) to
SQLAlchemy filters using `fastapi-filter`'s built-in `search_model_fields`.
"""

from typing import Any

from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import field_validator

from app.core.schemas import normalize_slug
from app.modules.essays.models import EssayPrompt
from app.modules.materials.models import StudyMaterial
from app.modules.quizzes.models import Quiz


class SearchFilterFields(Filter):
    """Shared filter query fields for study materials, quizzes, and essay prompts."""

    subject: str | None = None
    topic: str | None = None
    difficulty: str | None = None
    search: str | None = None

    @field_validator("subject", "topic", mode="after")
    @classmethod
    def _normalize_slug_fields(cls, value: str | None) -> Any:
        """Lowercase and trim filter slugs so `?subject=Math` matches `'math'`."""
        return normalize_slug(value)


class StudyMaterialFilter(SearchFilterFields):
    """Filters for StudyMaterial list queries."""

    class Constants(Filter.Constants):
        model = StudyMaterial
        search_model_fields = ["title", "content"]


class QuizFilter(SearchFilterFields):
    """Filters for Quiz list queries."""

    class Constants(Filter.Constants):
        model = Quiz
        search_model_fields = ["title", "topic"]


class EssayPromptFilter(SearchFilterFields):
    """Filters for EssayPrompt list queries."""

    class Constants(Filter.Constants):
        model = EssayPrompt
        search_model_fields = ["topic", "prompt_text"]
