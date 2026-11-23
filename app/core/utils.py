"""Shared pure utility helpers for vectors and percentage math."""

import math
from collections.abc import Sequence

from app.core.constants import EMBEDDING_DIM


def _l2_norm(values: Sequence[float]) -> float:
    """Compute Euclidean length of a vector, returning 1.0 for zero vectors."""
    sq_sum = 0.0
    for val in values:
        sq_sum += val * val
    return math.sqrt(sq_sum) or 1.0


def normalize_vector(raw_values: Sequence[float], dims: int | None = None) -> list[float]:
    """L2-normalize a vector to a fixed dimension count."""
    target_dims = dims if dims is not None else EMBEDDING_DIM
    vec = list(raw_values[:target_dims])
    padding = max(0, target_dims - len(vec))
    vec.extend([0.0] * padding)
    norm = _l2_norm(vec)
    return [x / norm for x in vec]


def calculate_percentage(score: int | float, max_score: int | float) -> float:
    """Convert raw `score / max_score` to a rounded percentage without zero-division."""
    if max_score <= 0:
        return 0.0
    return round((float(score) / float(max_score)) * 100.0, 1)


def average_percentage(pairs: Sequence[tuple[int | float, int | float]]) -> float:
    """Compute the mean percentage across `(score, max_score)` pairs."""
    if not pairs:
        return 0.0
    total = 0.0
    for score, max_score in pairs:
        total += calculate_percentage(score, max_score)
    return round(total / len(pairs), 1)
