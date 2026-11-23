"""Shared Pydantic schemas, normalized field types, and validation helpers."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, Field, StringConstraints

# Restrict values at validation time and generate exact OpenAPI enum schemas.
DifficultyLevel = Literal["easy", "medium", "hard"]
QuestionType = Literal["mcq", "fill_blank", "short_answer"]


def normalize_slug(value: Any) -> Any:
    """Trim whitespace and lowercase string slugs before validation."""
    if isinstance(value, str):
        return value.strip().lower()
    return value


def reject_null(value: Any) -> Any:
    """Reject explicit `null` for fields that are optional only in PATCH payloads."""
    if value is None:
        raise ValueError("Field cannot be null")
    return value


SlugField = Annotated[
    str,
    BeforeValidator(normalize_slug),
    StringConstraints(min_length=2, max_length=100),
]
# PATCH helpers: omitted fields stay unchanged, while explicit JSON null is rejected.
NonNullSlug = Annotated[SlugField, BeforeValidator(reject_null)]
NonNullDifficulty = Annotated[DifficultyLevel, BeforeValidator(reject_null)]


class HealthResponse(BaseModel):
    """Payload returned by `/health` and `/api/v1/health` readiness checks."""

    status: Literal["healthy"] = "healthy"
    service: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    """Consistent error envelope returned by all global exception handlers."""

    error: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
