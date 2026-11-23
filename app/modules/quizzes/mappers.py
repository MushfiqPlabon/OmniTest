"""ORM-to-schema mapping helpers for quizzes, questions, and student attempts."""

from app.core.utils import calculate_percentage
from app.modules.quizzes.models import Question, QuizAttempt
from app.modules.quizzes.schemas import QuestionCreate, UserAttemptSummaryResponse


def to_question_row(q: QuestionCreate, idx: int) -> Question:
    """Convert a validated `QuestionCreate` schema into a `Question` ORM entity."""
    return Question(
        type=q.type,
        prompt=q.prompt,
        options=q.options,
        correct_answer=q.correct_answer,
        explanation=q.explanation,
        order_num=q.order_num or idx,
    )


def to_user_attempt_summary(attempt: QuizAttempt) -> UserAttemptSummaryResponse:
    """Map a `QuizAttempt` ORM row to `UserAttemptSummaryResponse`."""
    return UserAttemptSummaryResponse(
        id=attempt.id,
        user_id=attempt.user_id,
        quiz_id=attempt.quiz_id,
        quiz_title=attempt.quiz.title if attempt.quiz else None,
        quiz_subject=attempt.quiz.subject if attempt.quiz else None,
        score=attempt.score,
        max_score=attempt.max_score,
        percentage=calculate_percentage(attempt.score, attempt.max_score),
        completed_at=attempt.completed_at,
    )
