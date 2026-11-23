"""Unit tests for quiz grading logic, anti-cheating checks, and hidden explanations."""

import pytest
from pydantic import ValidationError

from app.modules.quizzes.grading import grade_quiz_attempt, normalize_mcq_answer
from app.modules.quizzes.models import Question, Quiz
from app.modules.quizzes.schemas import AttemptCreate, QuestionResponse


def _sample_quiz() -> Quiz:
    q1 = Question(
        id=1,
        quiz_id=10,
        type="mcq",
        prompt="What is 2 + 2?",
        options=["A. 3", "B. 4", "C. 5", "D. 6"],
        correct_answer="B",
        explanation="2 + 2 = 4",
        order_num=1,
    )
    q2 = Question(
        id=2,
        quiz_id=10,
        type="short_answer",
        prompt="Capital of France?",
        options=None,
        correct_answer="Paris",
        explanation="Paris is the capital of France.",
        order_num=2,
    )
    return Quiz(id=10, title="Sample", subject="math", topic="basics", difficulty="easy", questions=[q1, q2])


def test_question_response_hides_correct_answer_and_explanation():
    fields = set(QuestionResponse.model_fields.keys())
    assert "correct_answer" not in fields
    assert "explanation" not in fields


def test_attempt_create_rejects_non_numeric_question_keys():
    with pytest.raises(ValidationError, match="integer string"):
        AttemptCreate(answers={"abc": "A"})


def test_duplicate_question_keys_cannot_inflate_score():
    quiz = _sample_quiz()
    score, max_score, pct, _, details = grade_quiz_attempt(quiz, {"1": "B", "01": "B", " 1 ": "B"})
    assert score == 1
    assert max_score == 2
    assert pct == 50.0
    # Unanswered question 2 still appears in details
    assert len(details) == 2
    assert details[1].question_id == 2
    assert details[1].student_answer == ""
    assert details[1].is_correct is False


def test_mcq_number_normalization():
    assert normalize_mcq_answer("2") == "B"
    assert normalize_mcq_answer(" c ") == "C"
