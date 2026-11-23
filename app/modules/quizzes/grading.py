"""Pure quiz grading helpers isolated from database and HTTP layers.

When it runs: Invoked by `QuizService.submit_attempt` when a student submits answers.
How & why: Normalizes MCQ numbers/letters (`1->A`), matches answers case-insensitively,
and computes feedback without SQLAlchemy or FastAPI so unit tests stay fast offline.
"""

from app.core.utils import calculate_percentage
from app.modules.quizzes.models import Question, Quiz
from app.modules.quizzes.schemas import AttemptDetailItem

_MCQ_NUMBERS = {"1": "A", "2": "B", "3": "C", "4": "D"}


def normalize_mcq_answer(answer: str) -> str:
    """Normalize MCQ inputs (`'1'` -> `'A'`, `'b'` -> `'B'`)."""
    cleaned = answer.strip().upper()
    return _MCQ_NUMBERS.get(cleaned, cleaned)


def _answers_match(question: Question, submitted: str) -> bool:
    """Compare student answer against stored answer using question-type rules."""
    if question.type == "mcq":
        return normalize_mcq_answer(question.correct_answer) == normalize_mcq_answer(submitted)
    return question.correct_answer.strip().upper() == submitted.strip().upper()


def _grade_question(question: Question, answer_by_qid: dict[int, str]) -> AttemptDetailItem:
    """Grade one question and construct its review breakdown item."""
    student_answer = answer_by_qid.get(question.id, "")
    is_correct = bool(student_answer) and _answers_match(question, student_answer)
    return AttemptDetailItem(
        question_id=question.id,
        prompt=question.prompt,
        student_answer=student_answer,
        correct_answer=question.correct_answer,
        is_correct=is_correct,
        explanation=question.explanation,
    )


def _build_feedback(percentage: float) -> str:
    """Return concise motivational feedback based on quiz percentage."""
    if percentage < 50:
        return "Needs review. Check explanations below."
    return "Good effort. Review missed topics and try again."


def grade_quiz_attempt(
    quiz: Quiz,
    submitted_answers: dict[str, str],
) -> tuple[int, int, float, str, list[AttemptDetailItem]]:
    """Grade submitted answers against `quiz.questions` and build per-question details."""
    answer_by_qid = {int(q_id.strip()): ans for q_id, ans in submitted_answers.items()}
    details = [_grade_question(question, answer_by_qid) for question in quiz.questions]
    correct_count = 0
    for item in details:
        if item.is_correct:
            correct_count += 1
    percentage = calculate_percentage(correct_count, len(quiz.questions))
    return correct_count, len(quiz.questions), percentage, _build_feedback(percentage), details
