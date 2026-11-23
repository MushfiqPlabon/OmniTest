"""Idempotent study material ingestion CLI for chunking and pgvector indexing.

When it runs: Executes on Docker container boot (`docker-compose.yml`) or manually.
How & why: Reads `data/materials/*.md`, skips unchanged files that already have stored
chunks, and only embeds new or edited guides so repeated runs save API quota.
"""

import asyncio
import sys
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.modules.materials.models import KnowledgeChunk, StudyMaterial
from app.modules.materials.repositories import MaterialRepository
from app.modules.materials.services import MaterialService

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "materials"


def _infer_subject(stem: str) -> str:
    """Guess a subject category from a markdown filename like `ged_math_fractions.md`."""
    if "math" in stem:
        return "math"
    if "grammar" in stem or "writing" in stem:
        return "writing"
    return "general"


def _extract_title(content: str, fallback_stem: str) -> str:
    """Use the first markdown heading line as the document title."""
    lines = content.splitlines()
    return lines[0].replace("#", "").strip() if lines else fallback_stem


async def _try_ingest(service: MaterialService, material_id: int, content: str, label: str) -> None:
    """Embed chunks best-effort so transient Gemini failures do not abort container boot."""
    try:
        await service.ingest_material_chunks(material_id, content)
    except Exception as exc:
        print(f"  [warn] Skipping embedding for '{label}': {exc}")


async def _update_existing_document(
    session: AsyncSession,
    service: MaterialService,
    existing: StudyMaterial,
    title: str,
    content: str,
    filename: str,
) -> None:
    """Skip unchanged documents or update text and re-embed changed files."""
    count_stmt = select(func.count(KnowledgeChunk.id)).where(KnowledgeChunk.material_id == existing.id)
    chunk_count = (await session.execute(count_stmt)).scalar_one()
    if existing.content == content and chunk_count > 0:
        print(f"  [skip] Unchanged '{title}' ({filename}) -> {chunk_count} chunk(s)")
        return
    existing.content = content
    await session.commit()
    await _try_ingest(service, existing.id, content, filename)
    print(f"  [ok] Updated '{title}' ({filename}) -> Material ID {existing.id}")


async def _create_new_document(
    repo: MaterialRepository,
    service: MaterialService,
    file_path: Path,
    title: str,
    content: str,
) -> None:
    """Insert a brand-new study material from markdown and embed its chunks."""
    material = StudyMaterial(
        title=title,
        subject=_infer_subject(file_path.stem),
        topic=file_path.stem.replace("_", " "),
        difficulty="medium",
        content=content,
        source=file_path.name,
    )
    saved = await repo.create(material)
    await _try_ingest(service, saved.id, saved.content, file_path.name)
    print(f"  [ok] Ingested '{title}' ({file_path.name}) -> Material ID {saved.id}")


async def _upsert_document(
    session: AsyncSession,
    repo: MaterialRepository,
    service: MaterialService,
    file_path: Path,
) -> None:
    """Insert or update one markdown document and rebuild its chunks only when text changed."""
    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        return
    title = _extract_title(content, file_path.stem)
    existing = (await session.execute(select(StudyMaterial).where(StudyMaterial.title == title))).scalars().first()
    if existing:
        await _update_existing_document(session, service, existing, title, content, file_path.name)
    else:
        await _create_new_document(repo, service, file_path, title, content)


async def ingest_documents() -> None:
    """Scan `data/materials/*.md` and ingest every markdown file into PostgreSQL."""
    if not DATA_DIR.exists():
        print(f"Directory {DATA_DIR} does not exist.")
        return

    print("Ingesting study material documents into RAG vector knowledge base...")
    async with AsyncSessionLocal() as session:
        repo = MaterialRepository(session)
        service = MaterialService(repo)
        for file_path in sorted(DATA_DIR.glob("*.md")):
            await _upsert_document(session, repo, service, file_path)
    print("Ingestion complete.")


if __name__ == "__main__":
    asyncio.run(ingest_documents())
