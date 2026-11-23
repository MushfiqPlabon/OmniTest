"""Gemini text embedding service for RAG chunk indexing and semantic search.

When it runs: During `scripts/ingest.py`, material saves/edits, and RAG query lookups.
How & why: Wraps each chunk in its own `types.Content` so batch calls on
`gemini-embedding-2` return one vector per chunk, then L2-normalizes to 384 dims.
"""

from collections.abc import Sequence
from typing import cast

from google.genai import types

from app.core.config import settings
from app.core.constants import EMBEDDING_DIM, GEMINI_BATCH_SIZE
from app.core.utils import normalize_vector
from app.integrations.llm.client import get_gemini_client


def _extract_vectors(resp: types.EmbedContentResponse) -> list[list[float]]:
    """Normalize every non-empty embedding vector returned by a Gemini batch call."""
    vectors: list[list[float]] = []
    for emb in resp.embeddings or []:
        if emb.values is not None:
            vectors.append(normalize_vector(emb.values))
    return vectors


class EmbeddingService:
    """Generates normalized 384-dimensional embeddings via Gemini `embed_content`."""

    async def embed_texts(self, texts: Sequence[str], *, task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        """Embed text chunks in batches using each item's own `Content` wrapper."""
        if not texts:
            return []

        client = get_gemini_client()
        config = types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM, task_type=task_type)
        results: list[list[float]] = []

        for idx in range(0, len(texts), GEMINI_BATCH_SIZE):
            chunk_slice = texts[idx : idx + GEMINI_BATCH_SIZE]
            # Wrapping each chunk as its own `Content` preserves 1-vector-per-chunk on `gemini-embedding-2`.
            batch: list[types.Content] = []
            for item in chunk_slice:
                batch.append(types.Content(parts=[types.Part.from_text(text=item)]))
            resp = await client.aio.models.embed_content(
                model=settings.GEMINI_EMBEDDING_MODEL,
                contents=cast(types.ContentListUnion, batch),
                config=config,
            )
            results.extend(_extract_vectors(resp))
        return results

    async def embed_query(self, query: str) -> list[float]:
        """Embed a single search query string into a 384-d unit vector."""
        vectors = await self.embed_texts([query], task_type="RETRIEVAL_QUERY")
        if not vectors:
            raise ValueError("Gemini returned no embedding vector for query")
        return vectors[0]


embedding_service = EmbeddingService()
