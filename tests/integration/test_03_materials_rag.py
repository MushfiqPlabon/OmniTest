"""Live integration tests for study materials CRUD, `?search=`, and pgvector RAG."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.integrations.embedding import embedding_service
from tests.integration.helpers import api

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_15_admin_creates_material(admin_headers):
    """POST /materials -> 201, material persisted to Postgres, then cleaned up."""
    r = await api(
        "post",
        "/api/v1/materials",
        headers=admin_headers,
        json={
            "title": "Test: Photosynthesis Basics",
            "subject": "science",
            "topic": "biology",
            "difficulty": "easy",
            "content": (
                "Photosynthesis is the process by which plants convert sunlight into energy. "
                "The chemical equation is: 6CO2 + 6H2O + light -> C6H12O6 + 6O2."
            ),
            "source": "GED Science Prep",
        },
    )
    assert r.status_code == 201, f"Create material failed: {r.text}"
    created_id = r.json()["id"]
    try:
        assert r.json()["title"] == "Test: Photosynthesis Basics"
    finally:
        await api("delete", f"/api/v1/materials/{created_id}", headers=admin_headers)


@pytest.mark.asyncio
async def test_16_list_materials_with_filter_and_search(student_headers, material_id):
    """GET /materials?subject=science&search=sunlight -> paged filtered results."""
    r = await api(
        "get",
        "/api/v1/materials",
        headers=student_headers,
        params={"subject": "science", "search": "sunlight", "page": 1, "size": 10},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["total"] >= 1
    assert {m["subject"] for m in data["items"]} == {"science"}


@pytest.mark.asyncio
async def test_17_get_material_by_id(student_headers, material_id):
    """GET /materials/{id} -> returns exact material from DB."""
    r = await api("get", f"/api/v1/materials/{material_id}", headers=student_headers)
    assert r.status_code == 200
    assert r.json()["id"] == material_id


@pytest.mark.asyncio
async def test_18_update_material(admin_headers, material_id):
    """PATCH /materials/{id} -> updated field persisted."""
    r = await api("patch", f"/api/v1/materials/{material_id}", headers=admin_headers, json={"difficulty": "medium"})
    assert r.status_code == 200
    assert r.json()["difficulty"] == "medium"


@pytest.mark.asyncio
async def test_19_get_nonexistent_material_returns_404(student_headers):
    """GET /materials/999999 -> 404 Not Found, clean JSON, no stack trace."""
    r = await api("get", "/api/v1/materials/999999", headers=student_headers)
    assert r.status_code == 404
    assert r.json()["error"] == "not_found"
    assert "traceback" not in r.text.lower()


@pytest.mark.asyncio
async def test_20_ingest_creates_knowledge_chunks(admin_headers, material_id):
    """Ingest endpoint chunks, embeds, and stores vectors in pgvector."""
    r = await api("post", f"/api/v1/materials/{material_id}/ingest", headers=admin_headers)
    assert r.status_code == 200, r.text
    assert r.json().get("chunks_created", 0) >= 1


@pytest.mark.asyncio
async def test_21_similarity_search_returns_relevant_chunk(material_id):
    """pgvector cosine search retrieves the correct chunk for a related query."""
    vecs = await embedding_service.embed_texts(["photosynthesis sunlight plants energy"])
    vec = vecs[0]

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.connect() as conn:
        rows = await conn.execute(
            text(
                "SELECT content, 1 - (embedding <=> CAST(:q AS vector)) AS similarity "
                "FROM knowledge_chunks ORDER BY similarity DESC LIMIT 1"
            ),
            {"q": str(vec)},
        )
        row = rows.fetchone()
        assert row is not None
        assert row.similarity > 0.3
        assert any(w in row.content.lower() for w in ["photosynthesis", "sunlight", "plants"])
    await engine.dispose()
