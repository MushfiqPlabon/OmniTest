"""Business logic for study guides, chunking, and pgvector RAG search.

When & how: Saves guides via `BaseRepository`, then splits text into 500-char
chunks (50 overlap) and embeds them on create, upload, or content edits.
Why: Softly warns on transient embedding failures so saving guides never aborts.
"""

import logging

from fastapi import UploadFile
from fastapi_pagination import Page, Params
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.constants import CHUNK_OVERLAP, CHUNK_SIZE
from app.filters import StudyMaterialFilter
from app.integrations.embedding import embedding_service
from app.modules.materials.models import StudyMaterial
from app.modules.materials.repositories import MaterialRepository
from app.modules.materials.schemas import (
    IngestResponse,
    KnowledgeChunkResponse,
    MaterialCreate,
    MaterialResponse,
    MaterialUpdate,
)
from app.modules.materials.uploads import parse_uploaded_material

logger = logging.getLogger("omnitest.materials")


class MaterialService:
    """Manages study guides and converts text content into searchable vector chunks."""

    def __init__(self, repo: MaterialRepository):
        self.repo = repo

    async def create_material(self, data: MaterialCreate, user_id: int | None = None) -> MaterialResponse:
        """Save a new study guide and immediately generate searchable vector chunks."""
        material = StudyMaterial(
            title=data.title,
            subject=data.subject,
            topic=data.topic,
            difficulty=data.difficulty,
            content=data.content,
            source=data.source,
            created_by=user_id,
        )
        saved = await self.repo.create(material)
        response = MaterialResponse.model_validate(saved)
        await self._try_ingest_chunks(response.id, response.content)
        return response

    async def upload_material(
        self,
        *,
        file: UploadFile,
        title: str,
        subject: str,
        topic: str,
        difficulty: str,
        user_id: int | None = None,
    ) -> MaterialResponse:
        """Parse an uploaded `.md`/`.txt` file and store it as a study material."""
        create_dto = await parse_uploaded_material(file, title, subject, topic, difficulty)
        return await self.create_material(create_dto, user_id=user_id)

    async def get_by_id(self, material_id: int) -> MaterialResponse:
        """Fetch one study guide or raise HTTP 404 NotFoundError."""
        material = await self.repo.get_or_404(material_id, "Study material")
        return MaterialResponse.model_validate(material)

    async def list_materials(
        self,
        filters: StudyMaterialFilter | None = None,
        params: Params | None = None,
    ) -> Page[MaterialResponse]:
        """Return paginated study guides matching optional filters and keyword search."""
        return await self.repo.list_filtered(filters=filters, params=params, schema=MaterialResponse)

    async def update_material(self, material_id: int, data: MaterialUpdate) -> MaterialResponse:
        """Partially update fields sent by the caller and re-embed chunks if content changed."""
        material = await self.repo.get_or_404(material_id, "Study material")
        update_dict = data.model_dump(exclude_unset=True)
        updated = await self.repo.update(material, update_dict)
        response = MaterialResponse.model_validate(updated)

        if "content" in update_dict:
            await self._try_ingest_chunks(response.id, response.content)
        return response

    async def delete_material(self, material_id: int) -> None:
        """Delete a study guide (child chunks cascade-delete in PostgreSQL)."""
        material = await self.repo.get_or_404(material_id, "Study material")
        await self.repo.delete(material)

    async def _try_ingest_chunks(self, material_id: int, content: str) -> None:
        """Best-effort chunk ingestion so transient API errors do not abort saves."""
        try:
            await self.ingest_material_chunks(material_id, content)
        except Exception as exc:
            logger.warning("Failed to ingest chunks for material %s: %s", material_id, exc)

    async def ingest_material_chunks(self, material_id: int, content: str) -> int:
        """Split material text into overlapping chunks, embed them, and replace stored vectors."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        raw_chunks = splitter.split_text(content)
        if not raw_chunks:
            return 0
        vectors = await embedding_service.embed_texts(raw_chunks)
        if len(vectors) != len(raw_chunks):
            raise ValueError("Embedding count did not match chunk count")

        chunk_tuples: list[tuple[str, int, list[float]]] = []
        for idx, chunk_text in enumerate(raw_chunks):
            chunk_tuples.append((chunk_text, idx, vectors[idx]))
        await self.repo.replace_chunks(material_id, chunk_tuples)
        return len(chunk_tuples)

    async def reingest_material(self, material_id: int) -> IngestResponse:
        """Regenerate chunk vectors for an existing material from its saved content."""
        material = await self.repo.get_or_404(material_id, "Study material")
        chunks_created = await self.ingest_material_chunks(material.id, material.content)
        return IngestResponse(material_id=material.id, chunks_created=chunks_created)

    async def search_chunks(
        self,
        query: str,
        limit: int = 5,
        min_similarity: float = 0.0,
    ) -> list[KnowledgeChunkResponse]:
        """Embed a query, run pgvector cosine similarity search, and return matching chunks."""
        query_vec = await embedding_service.embed_query(query)
        rows = await self.repo.search_similar_chunks(query_vec, limit=limit)
        results: list[KnowledgeChunkResponse] = []
        for chunk, material_title, similarity in rows:
            if similarity < min_similarity:
                continue
            results.append(
                KnowledgeChunkResponse(
                    id=chunk.id,
                    material_id=chunk.material_id,
                    material_title=material_title,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    similarity=round(similarity, 4),
                )
            )
        return results
