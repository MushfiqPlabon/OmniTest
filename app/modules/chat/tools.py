"""User-scoped chat tool factories for the AI Tutor.

When it runs: Called once per `POST /chat` turn by `ChatService.chat`.
How & why: Locks `user_id` inside closures so Gemini cannot request another
student's ID, and opens a fresh `AsyncSessionLocal()` per tool call to keep sessions isolated.
"""

from typing import Any

from app.core.database import AsyncSessionLocal
from app.integrations.llm.tools import (
    GenerateQuizArgs,
    GetProgressArgs,
    SearchMaterialsArgs,
    ToolSpec,
    generate_practice_quiz,
    get_student_progress,
    search_study_materials,
)
from app.modules.essays.repositories import EssayRepository
from app.modules.essays.services import EssayService
from app.modules.materials.repositories import MaterialRepository
from app.modules.materials.services import MaterialService
from app.modules.quizzes.repositories import QuizRepository
from app.modules.quizzes.services import QuizService


def _quiz_tool(user_id: int) -> ToolSpec:
    """Build `generate_practice_quiz` bound strictly to `user_id`."""

    async def _run(args: GenerateQuizArgs) -> dict[str, Any]:
        async with AsyncSessionLocal() as session:
            service = QuizService(QuizRepository(session))
            return await generate_practice_quiz(service, user_id, args)

    return ToolSpec(
        name="generate_practice_quiz",
        description="Generate and save a practice quiz for the student in the database.",
        args_schema=GenerateQuizArgs,
        handler=_run,
    )


def _progress_tool(user_id: int) -> ToolSpec:
    """Build `get_student_progress` bound strictly to `user_id`."""

    async def _run(args: GetProgressArgs) -> dict[str, Any]:
        async with AsyncSessionLocal() as session:
            quiz_svc = QuizService(QuizRepository(session))
            essay_svc = EssayService(EssayRepository(session))
            return await get_student_progress(quiz_svc, essay_svc, user_id, args)

    return ToolSpec(
        name="get_student_progress",
        description="Get the current student's quiz and essay progress analytics.",
        args_schema=GetProgressArgs,
        handler=_run,
    )


def _search_tool() -> ToolSpec:
    """Build the pgvector `search_study_materials` RAG tool."""

    async def _run(args: SearchMaterialsArgs) -> dict[str, Any]:
        async with AsyncSessionLocal() as session:
            service = MaterialService(MaterialRepository(session))
            return await search_study_materials(service, args)

    return ToolSpec(
        name="search_study_materials",
        description="Search study materials by semantic meaning using pgvector.",
        args_schema=SearchMaterialsArgs,
        handler=_run,
    )


def build_chat_tools(user_id: int) -> list[ToolSpec]:
    """Return the validated chat tool suite scoped to `user_id`."""
    return [_quiz_tool(user_id), _progress_tool(user_id), _search_tool()]
