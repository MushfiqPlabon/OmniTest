"""Curated starter GED and SAT essay prompts with 12-point rubrics."""

from typing import Any

from app.modules.essays.models import EssayPrompt

_PROMPT_SPECS: list[dict[str, Any]] = [
    {
        "subject": "writing",
        "topic": "persuasive_essay",
        "difficulty": "medium",
        "prompt_text": (
            "Read the following excerpt regarding renewable energy transition: "
            "'As urban centers grow, municipal reliance on centralized fossil energy grids becomes ecologically unstable. "
            "Decentralized solar micro-grids offer resilience, yet initial capital expenditure strains public budgets.' "
            "Write a response analyzing how the author builds an argument to convince municipal leaders to subsidize micro-grids."
        ),
        "rubric": {
            "max_score": 12,
            "criteria": [
                {"name": "Reading Comprehension", "max": 4, "desc": "Understanding of author's claims and evidence"},
                {
                    "name": "Analytical Depth",
                    "max": 4,
                    "desc": "Analysis of rhetoric, logical progression, and stylistic elements",
                },
                {
                    "name": "Writing & Cohesion",
                    "max": 4,
                    "desc": "Command of grammar, vocabulary, sentence variety, and transitions",
                },
            ],
        },
    },
    {
        "subject": "social_studies",
        "topic": "civics_history",
        "difficulty": "hard",
        "prompt_text": (
            "Analyze the balance of power between federal authority and state sovereignty in the United States constitutional framework. "
            "Evaluate whether Supreme Court precedents have expanded or curtailed executive discretion during times of crisis."
        ),
        "rubric": {
            "max_score": 12,
            "criteria": [
                {
                    "name": "Historical Evidence",
                    "max": 4,
                    "desc": "Accurate citations of constitutional principles and cases",
                },
                {"name": "Argumentation", "max": 4, "desc": "Coherent thesis supported by deductive reasoning"},
                {"name": "Clarity & Style", "max": 4, "desc": "Structured paragraphs and academic prose"},
            ],
        },
    },
]


def build_seed_prompts(admin_id: int | None) -> list[EssayPrompt]:
    """Build starter EssayPrompt ORM objects from `_PROMPT_SPECS`."""
    return [EssayPrompt(**spec, created_by=admin_id) for spec in _PROMPT_SPECS]
