"""Pydantic request and response schemas for study materials and RAG search chunks."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.core.schemas import DifficultyLevel, NonNullDifficulty, NonNullSlug, SlugField, reject_null


class MaterialCreate(BaseModel):
    """Request body for creating a new study material document."""

    title: str = Field(..., min_length=2, max_length=255)
    subject: SlugField
    topic: SlugField
    difficulty: DifficultyLevel = "medium"
    content: str = Field(..., min_length=10, max_length=200_000)
    source: str | None = Field(default=None, max_length=255)


class MaterialUpdate(BaseModel):
    """Partial update payload (`PATCH`); omitted fields stay unchanged, `source: null` clears source."""

    title: Annotated[str, BeforeValidator(reject_null), Field(min_length=2, max_length=255)] | None = None
    subject: NonNullSlug | None = None
    topic: NonNullSlug | None = None
    difficulty: NonNullDifficulty | None = None
    content: Annotated[str, BeforeValidator(reject_null), Field(min_length=10, max_length=200_000)] | None = None
    source: str | None = Field(default=None, max_length=255)


class MaterialResponse(BaseModel):
    """Public representation of a stored study material record."""

    id: int
    title: str
    subject: str
    topic: str
    difficulty: str
    content: str
    source: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeChunkResponse(BaseModel):
    """Single matched text chunk returned by pgvector similarity search."""

    id: int
    material_id: int
    material_title: str | None = None
    content: str
    chunk_index: int
    similarity: float | None = None

    model_config = ConfigDict(from_attributes=True)


class IngestResponse(BaseModel):
    """Confirmation payload after splitting and embedding a study material into chunks."""

    status: Literal["success"] = "success"
    material_id: int
    chunks_created: int = Field(ge=0)
