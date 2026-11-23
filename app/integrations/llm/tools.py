"""Canonical tool schemas, Gemini declaration builder, and DB-backed tool handlers.

Why this exists:
Both the AI tutor chat and the FastMCP server share these Pydantic-validated
tool handlers, ensuring one single source of truth for arguments and logic.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from google.genai import types
from pydantic import BaseModel, Field

from app.core.schemas import DifficultyLevel, QuestionType
from app.core.utils import average_percentage

if TYPE_CHECKING:
    from app.modules.essays.services import EssayService
    from app.modules.materials.services import MaterialService
    from app.modules.quizzes.services import QuizService


class GenerateQuizArgs(BaseModel):
    """Validated inputs for creating an AI-generated practice quiz."""

    subject: str = Field(..., min_length=2, max_length=100, description="Subject (e.g. math, science, writing)")
    topic: str = Field(..., min_length=2, max_length=100, description="Specific topic (e.g. algebra, genetics)")
    difficulty: DifficultyLevel = Field(default="medium", description="Difficulty: easy, medium, or hard")
    num_questions: int = Field(default=5, ge=1, le=10, description="Number of questions (1-10)")
    question_type: QuestionType = Field(default="mcq", description="Question format: mcq or short_answer")


class SearchMaterialsArgs(BaseModel):
    """Validated inputs for semantic vector search over study guides."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query for study materials")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum chunks to return (1-20)")


class GetProgressArgs(BaseModel):
    """Validated inputs for querying a student's quiz and essay progress."""

    subject: str | None = Field(default=None, max_length=100, description="Optional subject filter")


@dataclass(frozen=True)
class ToolSpec:
    """Explicit pairing of Gemini schema metadata with a validated async handler."""

    name: str
    description: str
    args_schema: type[BaseModel]
    handler: Callable[[Any], Awaitable[dict[str, Any]]]


def build_function_declaration(spec: ToolSpec) -> types.FunctionDeclaration:
    """Convert a `ToolSpec` into a Gemini `FunctionDeclaration` exposing only safe args."""
    return types.FunctionDeclaration(
        name=spec.name,
        description=spec.description,
        parameters_json_schema=spec.args_schema.model_json_schema(),
    )


async def generate_practice_quiz(
    quiz_service: QuizService,
    user_id: int,
    args: GenerateQuizArgs,
) -> dict[str, Any]:
    """Generate and persist a practice quiz via `QuizService`."""
    quiz = await quiz_service.generate_ai_practice_quiz(
        user_id=user_id,
        subject=args.subject,
        topic=args.topic,
        difficulty=args.difficulty,
        num_questions=args.num_questions,
        question_type=args.question_type,
    )
    return {
        "status": "success",
        "quiz_id": quiz.id,
        "title": quiz.title,
        "questions_count": len(quiz.questions),
    }


async def search_study_materials(
    material_service: MaterialService,
    args: SearchMaterialsArgs,
) -> dict[str, Any]:
    """Search study materials via `MaterialService` pgvector similarity."""
    chunks = await material_service.search_chunks(query=args.query, limit=args.limit)
    return {
        "status": "success",
        "results": [
            {
                "material_id": chunk.material_id,
                "title": chunk.material_title,
                "content_preview": chunk.content[:200],
                "similarity": chunk.similarity,
            }
            for chunk in chunks
        ],
    }


async def get_student_progress(
    quiz_service: QuizService,
    essay_service: EssayService,
    user_id: int,
    args: GetProgressArgs,
) -> dict[str, Any]:
    """Summarize quiz and essay analytics for one student, optionally filtered by subject."""
    clean_subject = args.subject.strip().lower() if args.subject else None
    quiz_attempts = await quiz_service.get_attempts(user_id=user_id, subject=clean_subject)
    essays = await essay_service.get_student_essays(user_id=user_id, subject=clean_subject)

    quiz_pairs = [(a.score, a.max_score) for a in quiz_attempts]
    essay_pairs = [(e.score, e.max_score) for e in essays]
    return {
        "status": "success",
        "subject_filter": clean_subject,
        "quiz_attempts": len(quiz_attempts),
        "avg_quiz_score": average_percentage(quiz_pairs),
        "essay_submissions": len(essays),
        "avg_essay_score": average_percentage(essay_pairs),
    }
