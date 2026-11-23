"""Pydantic request and response schemas for quizzes, questions, and graded attempts.

Security separation:
`QuestionResponse` omits both `correct_answer` and `explanation` while taking
a quiz; answers and explanations are revealed in `AttemptResponse` only after
submission.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

from app.core.schemas import DifficultyLevel, NonNullDifficulty, NonNullSlug, QuestionType, SlugField, reject_null


class QuestionCreate(BaseModel):
    """Input schema for one question when creating a quiz."""

    type: QuestionType = "mcq"
    prompt: str = Field(..., min_length=3)
    options: list[str] | None = None
    correct_answer: str = Field(..., min_length=1)
    explanation: str | None = None
    order_num: int = 1


class QuestionResponse(BaseModel):
    """Question returned to students taking a quiz (hides `correct_answer` and `explanation`)."""

    id: int
    quiz_id: int
    type: str
    prompt: str
    options: list[str] | None
    order_num: int

    model_config = ConfigDict(from_attributes=True)


class QuizCreate(BaseModel):
    """Request body for creating a quiz along with its questions."""

    title: str = Field(..., min_length=2, max_length=255)
    subject: SlugField
    topic: SlugField
    difficulty: DifficultyLevel = "medium"
    questions: list[QuestionCreate] = Field(default_factory=list)


class QuizUpdate(BaseModel):
    """Partial `PATCH` payload for updating quiz metadata."""

    title: Annotated[str, BeforeValidator(reject_null), Field(min_length=2, max_length=255)] | None = None
    subject: NonNullSlug | None = None
    topic: NonNullSlug | None = None
    difficulty: NonNullDifficulty | None = None


class QuizResponse(BaseModel):
    """Summary metadata for one quiz without its nested question list."""

    id: int
    title: str
    subject: str
    topic: str
    difficulty: str
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuizWithQuestionsResponse(QuizResponse):
    """Full quiz payload including ordered questions."""

    questions: list[QuestionResponse] = Field(default_factory=list)


class AttemptCreate(BaseModel):
    """Student answers keyed by numeric question ID strings."""

    answers: dict[str, str] = Field(..., description="Mapping of question_id to student answer string")

    @field_validator("answers", mode="after")
    @classmethod
    def _validate_question_id_keys(cls, value: dict[str, str]) -> dict[str, str]:
        """Ensure every answer key parses as an integer question ID (returns 422 instead of 500)."""
        for raw_key in value:
            try:
                int(raw_key.strip())
            except ValueError:
                raise ValueError(f"Question ID key '{raw_key}' must be an integer string") from None
        return value


class AttemptDetailItem(BaseModel):
    """Per-question grading breakdown returned after submitting a quiz."""

    question_id: int
    prompt: str
    student_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str | None = None


class AttemptResponse(BaseModel):
    """Full graded quiz result including percentage score and per-question feedback."""

    id: int
    quiz_id: int
    user_id: int
    score: int
    max_score: int
    percentage: float
    feedback: str
    details: list[AttemptDetailItem]
    completed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttemptSummaryResponse(BaseModel):
    """Compact summary row used on `GET /quizzes/{id}/attempts`."""

    id: int
    user_id: int
    score: int
    max_score: int
    completed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserAttemptSummaryResponse(AttemptSummaryResponse):
    """Attempt summary enriched with parent quiz metadata for user analytics."""

    quiz_id: int
    quiz_title: str | None = None
    quiz_subject: str | None = None
    percentage: float = 0.0
