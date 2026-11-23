"""FastAPI dependency factories for the study materials module.

Wires `get_db_session()` -> `MaterialRepository` -> `MaterialService` for each
incoming HTTP request so controllers receive a ready-to-use service instance.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.modules.materials.repositories import MaterialRepository
from app.modules.materials.services import MaterialService


def get_material_repo(session: AsyncSession = Depends(get_db_session)) -> MaterialRepository:
    """Create a per-request repository bound to the active database session."""
    return MaterialRepository(session)


def get_material_service(repo: MaterialRepository = Depends(get_material_repo)) -> MaterialService:
    """Create a per-request `MaterialService` backed by `MaterialRepository`."""
    return MaterialService(repo)
