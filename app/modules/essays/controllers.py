"""HTTP endpoints for essay prompts and AI essay grading (`/api/v1/essays`)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params

from app.core.constants import DEFAULT_HISTORY_LIMIT, MAX_HISTORY_LIMIT
from app.filters import EssayPromptFilter
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.auth.models import User
from app.modules.essays.dependencies import get_essay_service
from app.modules.essays.schemas import EssayResponse, EssaySubmit, PromptCreate, PromptResponse, PromptUpdate
from app.modules.essays.services import EssayService

router = APIRouter(prefix="/essays", tags=["Essay Practice & Evaluation"])


@router.post("/prompts", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    payload: PromptCreate,
    current_user: Annotated[User, Depends(require_admin)],
    service: Annotated[EssayService, Depends(get_essay_service)],
) -> PromptResponse:
    """Create a new essay writing prompt with a scoring rubric (admin only)."""
    return await service.create_prompt(payload, user_id=current_user.id)


@router.get("/prompts", response_model=Page[PromptResponse], status_code=status.HTTP_200_OK)
async def list_prompts(
    service: Annotated[EssayService, Depends(get_essay_service)],
    _: Annotated[User, Depends(get_current_user)],
    filters: Annotated[EssayPromptFilter, FilterDepends(EssayPromptFilter)],
    params: Annotated[Params, Depends()],
) -> Page[PromptResponse]:
    """List available essay prompts with pagination and subject/topic/difficulty/keyword filters."""
    return await service.list_prompts(filters=filters, params=params)


@router.get("/prompts/{prompt_id}", response_model=PromptResponse, status_code=status.HTTP_200_OK)
async def get_prompt(
    prompt_id: int,
    service: Annotated[EssayService, Depends(get_essay_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> PromptResponse:
    """Fetch a single essay prompt and its grading rubric by ID."""
    return await service.get_prompt_by_id(prompt_id)


@router.patch("/prompts/{prompt_id}", response_model=PromptResponse, status_code=status.HTTP_200_OK)
async def update_prompt(
    prompt_id: int,
    payload: PromptUpdate,
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[EssayService, Depends(get_essay_service)],
) -> PromptResponse:
    """Partially update an essay prompt's text, metadata, or rubric (admin only)."""
    return await service.update_prompt(prompt_id, payload)


@router.delete("/prompts/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: int,
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[EssayService, Depends(get_essay_service)],
) -> None:
    """Delete an essay prompt and all student essays written for it (admin only)."""
    await service.delete_prompt(prompt_id)


@router.post("/prompts/{prompt_id}/submit", response_model=EssayResponse, status_code=status.HTTP_201_CREATED)
async def submit_essay(
    prompt_id: int,
    payload: EssaySubmit,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[EssayService, Depends(get_essay_service)],
) -> EssayResponse:
    """Grade the student's essay submission via Gemini and store feedback & scores."""
    return await service.evaluate_and_submit_essay(prompt_id, current_user.id, payload)


@router.get("/my", response_model=list[EssayResponse], status_code=status.HTTP_200_OK)
async def get_my_essays(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[EssayService, Depends(get_essay_service)],
    limit: Annotated[int, Query(ge=1, le=MAX_HISTORY_LIMIT)] = DEFAULT_HISTORY_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[EssayResponse]:
    """Return graded essay submissions written by the logged-in user."""
    return await service.get_student_essays(current_user.id, limit=limit, offset=offset)
