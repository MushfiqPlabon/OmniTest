"""Business logic for quiz CRUD, attempt grading, and AI quiz generation.

When & how: Manages quiz authoring and listing, scores student submissions via
pure helpers in `grading.py`, and generates validated quizzes via Gemini.
Why: Grades answers deterministically on the server so students cannot tamper with keys.
"""

from fastapi_pagination import Page, Params

from app.core.constants import DEFAULT_HISTORY_LIMIT
from app.core.database import release_transaction
from app.filters import QuizFilter
from app.modules.auth.models import User
from app.modules.quizzes.generator import generate_quiz_questions, normalize_quiz_options
from app.modules.quizzes.grading import grade_quiz_attempt
from app.modules.quizzes.mappers import to_question_row, to_user_attempt_summary
from app.modules.quizzes.models import Quiz, QuizAttempt
from app.modules.quizzes.repositories import QuizRepository
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


class QuizService:
    """Coordinates quiz CRUD, attempt scoring, and AI practice quiz generation."""

    def __init__(self, repo: QuizRepository):
        self.repo = repo

    async def create_quiz(self, data: QuizCreate, user_id: int | None = None) -> QuizWithQuestionsResponse:
        """Persist a new quiz along with its ordered list of questions."""
        quiz = Quiz(
            title=data.title,
            subject=data.subject,
            topic=data.topic,
            difficulty=data.difficulty,
            created_by=user_id,
            questions=[to_question_row(q, idx) for idx, q in enumerate(data.questions, start=1)],
        )
        saved = await self.repo.create(quiz)
        return QuizWithQuestionsResponse.model_validate(saved)

    async def get_quiz_by_id(self, quiz_id: int) -> QuizWithQuestionsResponse:
        """Load one quiz with its questions or raise HTTP 404 NotFoundError."""
        quiz = await self.repo.get_or_404(quiz_id, "Quiz")
        return QuizWithQuestionsResponse.model_validate(quiz)

    async def list_quizzes(
        self,
        filters: QuizFilter | None = None,
        params: Params | None = None,
    ) -> Page[QuizResponse]:
        """Return paginated quizzes matching optional filters and keyword search."""
        return await self.repo.list_filtered(filters=filters, params=params, schema=QuizResponse)

    async def update_quiz(self, quiz_id: int, data: QuizUpdate) -> QuizResponse:
        """Partially update quiz metadata."""
        quiz = await self.repo.get_or_404(quiz_id, "Quiz")
        updated = await self.repo.update(quiz, data.model_dump(exclude_unset=True))
        return QuizResponse.model_validate(updated)

    async def delete_quiz(self, quiz_id: int) -> None:
        """Delete a quiz and cascade-delete its questions and attempts."""
        quiz = await self.repo.get_or_404(quiz_id, "Quiz")
        await self.repo.delete(quiz)

    async def submit_attempt(self, quiz_id: int, user_id: int, data: AttemptCreate) -> AttemptResponse:
        """Grade a student's quiz answers against DB questions and save the attempt."""
        quiz = await self.repo.get_or_404(quiz_id, "Quiz")
        score, max_score, percentage, feedback, details = grade_quiz_attempt(quiz, data.answers)
        row = QuizAttempt(quiz_id=quiz_id, user_id=user_id, score=score, max_score=max_score, answers=data.answers)
        attempt = await self.repo.create_attempt(row)
        return AttemptResponse(
            id=attempt.id,
            quiz_id=attempt.quiz_id,
            user_id=attempt.user_id,
            score=score,
            max_score=max_score,
            percentage=percentage,
            feedback=feedback,
            details=details,
            completed_at=attempt.completed_at,
        )

    async def get_attempts(
        self,
        user_id: int | None = None,
        quiz_id: int | None = None,
        subject: str | None = None,
        limit: int = DEFAULT_HISTORY_LIMIT,
        offset: int = 0,
    ) -> list[UserAttemptSummaryResponse]:
        """Return quiz attempt history enriched with parent quiz metadata."""
        attempts = await self.repo.get_attempts(
            quiz_id=quiz_id,
            user_id=user_id,
            subject=subject,
            limit=limit,
            offset=offset,
        )
        return [to_user_attempt_summary(a) for a in attempts]

    async def get_attempts_for_quiz(
        self,
        quiz_id: int,
        current_user: User,
        limit: int = DEFAULT_HISTORY_LIMIT,
        offset: int = 0,
    ) -> list[AttemptSummaryResponse]:
        """Return attempts for an existing quiz (admins see all; students see only theirs)."""
        await self.repo.get_or_404(quiz_id, "Quiz")
        is_admin = bool(current_user.role and current_user.role.name == "admin")
        target_user_id = None if is_admin else current_user.id
        attempts = await self.repo.get_attempts(quiz_id=quiz_id, user_id=target_user_id, limit=limit, offset=offset)
        return [AttemptSummaryResponse.model_validate(a) for a in attempts]

    async def generate_ai_practice_quiz(
        self,
        user_id: int,
        subject: str,
        topic: str,
        difficulty: str = "medium",
        num_questions: int = 5,
        question_type: str = "mcq",
    ) -> QuizWithQuestionsResponse:
        """Generate practice questions via Gemini, validate, save to PostgreSQL, and return."""
        clean_diff, clean_num, clean_qtype = normalize_quiz_options(difficulty, num_questions, question_type)
        # End the read transaction before waiting on Gemini so Postgres pool connections stay free.
        await release_transaction(self.repo.session)

        questions = await generate_quiz_questions(subject, topic, clean_diff, clean_num, clean_qtype)
        quiz_dto = QuizCreate(
            title=f"AI Practice: {topic.strip().title()} ({subject.strip().title()})",
            subject=subject,
            topic=topic,
            difficulty=clean_diff,
            questions=questions,
        )
        return await self.create_quiz(quiz_dto, user_id=user_id)
