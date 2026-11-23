"""Pydantic schemas for essay prompts, scoring rubrics, student submissions, and Gemini evaluation."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.core.schemas import DifficultyLevel, NonNullDifficulty, NonNullSlug, SlugField, reject_null


class RubricCriterion(BaseModel):
    """One graded dimension inside a rubric (e.g. Reading Comprehension up to 4 pts)."""

    name: str = Field(..., min_length=1, max_length=100)
    max: int = Field(ge=1)
    desc: str = ""


class EssayRubric(BaseModel):
    """Structured scoring rubric attached to each essay prompt."""

    max_score: int = Field(default=12, ge=1)
    criteria: list[RubricCriterion] = Field(default_factory=list)


def default_essay_rubric() -> EssayRubric:
    """Return the standard 12-point GED/SAT 3-part rubric."""
    return EssayRubric(
        max_score=12,
        criteria=[
            RubricCriterion(name="Reading Comprehension", max=4, desc="Evidence understanding"),
            RubricCriterion(name="Analysis & Reasoning", max=4, desc="Logic and critical thinking"),
            RubricCriterion(name="Writing & Style", max=4, desc="Clarity, grammar, structure"),
        ],
    )


class PromptCreate(BaseModel):
    """Request body for creating a new essay prompt."""

    subject: SlugField
    topic: SlugField
    prompt_text: str = Field(..., min_length=10)
    rubric: EssayRubric = Field(default_factory=default_essay_rubric)
    difficulty: DifficultyLevel = "medium"


class PromptUpdate(BaseModel):
    """Partial `PATCH` payload for editing an existing essay prompt."""

    subject: NonNullSlug | None = None
    topic: NonNullSlug | None = None
    prompt_text: Annotated[str, BeforeValidator(reject_null), Field(min_length=10)] | None = None
    rubric: Annotated[EssayRubric, BeforeValidator(reject_null)] | None = None
    difficulty: NonNullDifficulty | None = None


class PromptResponse(BaseModel):
    """Public representation of a stored essay prompt and its rubric."""

    id: int
    subject: str
    topic: str
    prompt_text: str
    rubric: EssayRubric
    difficulty: str
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EssaySubmit(BaseModel):
    """Student essay submission body (bounded between 20 and 15,000 chars)."""

    response_text: str = Field(..., min_length=20, max_length=15000, description="Student essay body text")


class CriterionScore(BaseModel):
    """Single rubric criterion score returned as a list item by Gemini JSON output."""

    # List items avoid open `dict[str, float]` schemas that Gemini constrained decoding rejects.
    name: str
    score: float


class EssayEvaluationResult(BaseModel):
    """Validated JSON structure returned by Gemini when grading a student essay."""

    score: int = Field(ge=0)
    max_score: int = Field(ge=1)
    criteria_scores: list[CriterionScore] = Field(default_factory=list)
    feedback: str = Field(..., min_length=1)


class EssayResponse(BaseModel):
    """Saved essay grade, criterion breakdown, and feedback returned to the student."""

    id: int
    user_id: int
    prompt_id: int
    subject: str | None = None
    response_text: str
    score: int
    max_score: int
    feedback: str
    criteria_scores: dict[str, float] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
