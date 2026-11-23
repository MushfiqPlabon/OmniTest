"""Database queries for study materials and pgvector RAG similarity search.

When it runs: During material updates/uploads and RAG vector lookups from chat or MCP.
How & why: Replaces stored vectors cleanly per guide and queries the HNSW
cosine index (`<=>`) via PostgreSQL instead of loading vectors into Python.
"""

from typing import Any

from sqlalchemy import delete, select

from app.core.repository import BaseRepository
from app.modules.materials.models import KnowledgeChunk, StudyMaterial


class MaterialRepository(BaseRepository):
    """Inherits CRUD/filtering from `BaseRepository` and adds RAG chunk indexing & pgvector search."""

    model = StudyMaterial

    async def replace_chunks(
        self, material_id: int, chunks: list[tuple[str, int, list[float]]]
    ) -> list[KnowledgeChunk]:
        """Delete existing chunks for one material and insert newly embedded vectors."""
        await self.session.execute(delete(KnowledgeChunk).where(KnowledgeChunk.material_id == material_id))

        new_chunks = [
            KnowledgeChunk(
                material_id=material_id,
                content=text,
                chunk_index=idx,
                embedding=vec,
            )
            for text, idx, vec in chunks
        ]
        self.session.add_all(new_chunks)
        await self.session.commit()
        return new_chunks

    async def search_similar_chunks(
        self, query_vec: list[float], limit: int = 5
    ) -> list[tuple[KnowledgeChunk, str | None, float]]:
        """Find the closest chunks by vector meaning using the pgvector HNSW cosine index."""
        # Convert pgvector cosine distance (0..2) into similarity (<= 1.0) so thresholds read clearly.
        distance_col: Any = KnowledgeChunk.embedding.cosine_distance(query_vec)
        similarity_col = (1.0 - distance_col).label("similarity")
        stmt = (
            select(KnowledgeChunk, StudyMaterial.title, similarity_col)
            .outerjoin(StudyMaterial, KnowledgeChunk.material_id == StudyMaterial.id)
            .where(KnowledgeChunk.embedding.is_not(None))
            .order_by(distance_col.asc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return [(chunk, title, float(sim)) for chunk, title, sim in res.all()]
