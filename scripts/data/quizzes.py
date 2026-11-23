"""Curated starter GED and SAT practice quizzes for `scripts/seed.py`."""

from typing import Any

from app.modules.quizzes.models import Question, Quiz

_QUIZ_SPECS: list[dict[str, Any]] = [
    {
        "title": "GED Algebra & Slope Fundamentals",
        "subject": "math",
        "topic": "algebra",
        "difficulty": "medium",
        "questions": [
            (
                "What is the slope of a line passing through (2, 3) and (6, 11)?",
                ["A. 2", "B. 4", "C. 1/2", "D. 8"],
                "A",
                "m = (11 - 3) / (6 - 2) = 8 / 4 = 2.",
            ),
            (
                "If a line has equation y = -3x + 7, what is the slope of a perpendicular line?",
                ["A. -3", "B. 3", "C. 1/3", "D. -1/3"],
                "C",
                "Perpendicular lines have negative reciprocal slopes: -1 / (-3) = 1/3.",
            ),
            (
                "What is the y-intercept of the line given by 2x + 4y = 16?",
                ["A. (0, 8)", "B. (0, 4)", "C. (0, 2)", "D. (0, 16)"],
                "B",
                "Set x = 0: 4y = 16 -> y = 4. Y-intercept is (0, 4).",
            ),
        ],
    },
    {
        "title": "SAT Reading Evidence & Synthesis",
        "subject": "reading",
        "topic": "main_idea",
        "difficulty": "hard",
        "questions": [
            (
                "Which characteristic most frequently signals an incorrect choice on SAT Reading main idea questions?",
                [
                    "A. Paraphrased phrasing",
                    "B. Extreme categorical words like 'always' or 'never'",
                    "C. Moderate qualifying language",
                    "D. Reference to the author's primary conclusion",
                ],
                "B",
                "Standardized reading tests favor nuanced, qualified arguments over extreme absolutes.",
            ),
            (
                "In SAT bulleted rhetorical synthesis questions, what should the test-taker read first?",
                [
                    "A. The entire passage introduction",
                    "B. The bulleted research notes",
                    "C. The student's specific rhetorical goal",
                    "D. The final answer choice",
                ],
                "C",
                "Reading the student's goal first clarifies what specific evidence must be emphasized.",
            ),
        ],
    },
    {
        "title": "GED Biology & Cellular Energy",
        "subject": "science",
        "topic": "biology",
        "difficulty": "medium",
        "questions": [
            (
                "Which organelle is the primary site of ATP generation in cellular respiration?",
                ["A. Chloroplast", "B. Ribosome", "C. Mitochondria", "D. Endoplasmic reticulum"],
                "C",
                "Mitochondria are the organelles responsible for aerobic ATP synthesis.",
            ),
            (
                "What are the primary output products of plant photosynthesis?",
                [
                    "A. Carbon dioxide and water",
                    "B. Glucose and oxygen",
                    "C. Nitrogen and ATP",
                    "D. Lactic acid and sunlight",
                ],
                "B",
                "Photosynthesis equation: 6CO2 + 6H2O + light -> C6H12O6 (glucose) + 6O2 (oxygen).",
            ),
        ],
    },
]


def build_seed_quizzes(admin_id: int | None) -> list[Quiz]:
    """Build starter GED/SAT Quiz ORM objects from `_QUIZ_SPECS`."""
    quizzes: list[Quiz] = []
    for spec in _QUIZ_SPECS:
        questions = [
            Question(
                type="mcq",
                prompt=prompt,
                options=options,
                correct_answer=answer,
                explanation=explanation,
                order_num=idx,
            )
            for idx, (prompt, options, answer, explanation) in enumerate(spec["questions"], start=1)
        ]
        quizzes.append(
            Quiz(
                title=spec["title"],
                subject=spec["subject"],
                topic=spec["topic"],
                difficulty=spec["difficulty"],
                created_by=admin_id,
                questions=questions,
            )
        )
    return quizzes
