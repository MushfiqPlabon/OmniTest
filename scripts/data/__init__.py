"""Starter curriculum data builders for `scripts/seed.py`."""

from scripts.data.materials import MATERIALS_DATA
from scripts.data.prompts import build_seed_prompts
from scripts.data.quizzes import build_seed_quizzes

__all__ = ["MATERIALS_DATA", "build_seed_prompts", "build_seed_quizzes"]
