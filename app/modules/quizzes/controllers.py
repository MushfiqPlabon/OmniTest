"""HTTP endpoints for practice quizzes, student submissions, and attempt history (`/api/v1/quizzes`)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params

from app.core.constants import DEFAULT_HISTORY_LIMIT, MAX_HISTORY_LIMIT
from app.filters import QuizFilter
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.auth.models import User
from app.modules.quizzes.dependencies import get_quiz_service
from app.modules.quizzes.schemas import (
    AttemptCreate,
    AttemptResponse,
    AttemptSummaryResponse,
    QuizCreate,
    QuizResponse,
    QuizUpdate,
    QuizWithQuestionsResponse,
    UserAttemptSummaryResponse,
)
from app.modules.quizzes.services import QuizService

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.post("", response_model=QuizWithQuestionsResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    payload: QuizCreate,
    current_user: Annotated[User, Depends(require_admin)],
    service: Annotated[QuizService, Depends(get_quiz_service)],
) -> QuizWithQuestionsResponse:
    """Create a quiz together with its list of questions (admin only)."""
    return await service.create_quiz(payload, user_id=current_user.id)


@router.get("", response_model=Page[QuizResponse], status_code=status.HTTP_200_OK)
async def list_quizzes(
    service: Annotated[QuizService, Depends(get_quiz_service)],
    _: Annotated[User, Depends(get_current_user)],
    filters: Annotated[QuizFilter, FilterDepends(QuizFilter)],
    params: Annotated[Params, Depends()],
) -> Page[QuizResponse]:
    """List quizzes with optional subject, topic, difficulty, keyword search, and paging."""
    return await service.list_quizzes(filters=filters, params=params)


# `/attempts/my` stays above `/{quiz_id}` so `"attempts"` is never matched as an integer ID.
@router.get("/attempts/my", response_model=list[UserAttemptSummaryResponse], status_code=status.HTTP_200_OK)
async def list_my_quiz_attempts(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[QuizService, Depends(get_quiz_service)],
    limit: Annotated[int, Query(ge=1, le=MAX_HISTORY_LIMIT)] = DEFAULT_HISTORY_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[UserAttemptSummaryResponse]:
    """Return past quiz attempts for the currently logged-in student."""
    return await service.get_attempts(user_id=current_user.id, limit=limit, offset=offset)


@router.get("/{quiz_id}", response_model=QuizWithQuestionsResponse, status_code=status.HTTP_200_OK)
async def get_quiz(
    quiz_id: int,
    service: Annotated[QuizService, Depends(get_quiz_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> QuizWithQuestionsResponse:
    """Load one quiz with its questions (correct answers and explanations stay hidden)."""
    return await service.get_quiz_by_id(quiz_id)


@router.patch("/{quiz_id}", response_model=QuizResponse, status_code=status.HTTP_200_OK)
async def update_quiz(
    quiz_id: int,
    payload: QuizUpdate,
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[QuizService, Depends(get_quiz_service)],
) -> QuizResponse:
    """Partially update quiz metadata (admin only)."""
    return await service.update_quiz(quiz_id, payload)


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: int,
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[QuizService, Depends(get_quiz_service)],
) -> None:
    """Delete a quiz plus its questions and recorded attempts (admin only)."""
    await service.delete_quiz(quiz_id)


@router.post("/{quiz_id}/attempt", response_model=AttemptResponse, status_code=status.HTTP_201_CREATED)
async def submit_quiz_attempt(
    quiz_id: int,
    payload: AttemptCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[QuizService, Depends(get_quiz_service)],
) -> AttemptResponse:
    """Grade the student's submitted quiz answers and persist the score."""
    return await service.submit_attempt(quiz_id, current_user.id, payload)


@router.get("/{quiz_id}/attempts", response_model=list[AttemptSummaryResponse], status_code=status.HTTP_200_OK)
async def get_quiz_attempts(
    quiz_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[QuizService, Depends(get_quiz_service)],
    limit: Annotated[int, Query(ge=1, le=MAX_HISTORY_LIMIT)] = DEFAULT_HISTORY_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AttemptSummaryResponse]:
    """List attempts for one quiz: admins see all students; students see only their own."""
    return await service.get_attempts_for_quiz(quiz_id, current_user, limit=limit, offset=offset)
