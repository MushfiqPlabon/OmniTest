"""AI practice quiz generation helper backed by Gemini structured JSON output."""

from app.core.schemas import DifficultyLevel, QuestionType
from app.integrations.llm.structured import generate_structured
from app.modules.quizzes.grading import normalize_mcq_answer
from app.modules.quizzes.schemas import QuestionCreate

MAX_QUESTIONS_PER_QUIZ = 10
_VALID_DIFFICULTIES: dict[str, DifficultyLevel] = {"easy": "easy", "medium": "medium", "hard": "hard"}
_VALID_QTYPES: dict[str, QuestionType] = {
    "mcq": "mcq",
    "fill_blank": "fill_blank",
    "short_answer": "short_answer",
}


def normalize_quiz_options(
    difficulty: str,
    num_questions: int,
    question_type: str,
) -> tuple[DifficultyLevel, int, QuestionType]:
    """Clamp question count and map difficulty/type strings onto allowed literals."""
    clean_diff = _VALID_DIFFICULTIES.get(difficulty.strip().lower(), "medium")
    clean_qtype = _VALID_QTYPES.get(question_type.strip().lower(), "mcq")
    clean_num = max(1, min(num_questions, MAX_QUESTIONS_PER_QUIZ))
    return clean_diff, clean_num, clean_qtype


def _build_quiz_prompt(
    subject: str,
    topic: str,
    difficulty: DifficultyLevel,
    num_questions: int,
    question_type: QuestionType,
) -> str:
    """Build the structured JSON generation prompt for practice questions."""
    format_instruction = (
        "Return ONLY a JSON array of question objects. Each object must have: "
        "type (mcq|fill_blank|short_answer), prompt (string), options (array|null), "
        "correct_answer (string), explanation (string), order_num (int). "
        "For mcq, provide 4 options labeled A-D and set correct_answer to a single letter A-D."
    )
    return (
        f"Generate {num_questions} {difficulty} {question_type} questions about {topic} ({subject}).\n"
        f"{format_instruction}"
    )


async def generate_quiz_questions(
    subject: str,
    topic: str,
    difficulty: DifficultyLevel,
    num_questions: int,
    question_type: QuestionType,
) -> list[QuestionCreate]:
    """Generate and normalize a validated list of practice questions via Gemini."""
    prompt = _build_quiz_prompt(subject, topic, difficulty, num_questions, question_type)
    questions = await generate_structured(prompt, list[QuestionCreate])
    for item in questions:
        if item.type == "mcq":
            item.correct_answer = normalize_mcq_answer(item.correct_answer)
    return questions
