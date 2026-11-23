"""HTTP endpoints for study guides and file uploads (`/api/v1/materials`).

When it runs: Handles incoming HTTP requests for reading, creating, uploading,
updating, deleting, or re-indexing curriculum materials.
How & why: Stays strictly at the HTTP layer (`Depends`, status codes, filtering,
pagination), restricting all writes to `require_admin` while signed-in users can read.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params

from app.core.schemas import DifficultyLevel
from app.filters import StudyMaterialFilter
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.auth.models import User
from app.modules.materials.dependencies import get_material_service
from app.modules.materials.schemas import IngestResponse, MaterialCreate, MaterialResponse, MaterialUpdate
from app.modules.materials.services import MaterialService

router = APIRouter(prefix="/materials", tags=["Study Materials"])


@router.get("", response_model=Page[MaterialResponse], status_code=status.HTTP_200_OK)
async def list_materials(
    service: Annotated[MaterialService, Depends(get_material_service)],
    _: Annotated[User, Depends(get_current_user)],
    filters: Annotated[StudyMaterialFilter, FilterDepends(StudyMaterialFilter)],
    params: Annotated[Params, Depends()],
) -> Page[MaterialResponse]:
    """List study materials with optional subject, topic, difficulty, keyword search, and paging."""
    return await service.list_materials(filters=filters, params=params)


@router.post("", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_material(
    payload: MaterialCreate,
    current_user: Annotated[User, Depends(require_admin)],
    service: Annotated[MaterialService, Depends(get_material_service)],
) -> MaterialResponse:
    """Create a new study material from a JSON body (admin only)."""
    return await service.create_material(payload, user_id=current_user.id)


@router.post("/upload", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def upload_material_file(
    title: Annotated[str, Form()],
    subject: Annotated[str, Form()],
    topic: Annotated[str, Form()],
    current_user: Annotated[User, Depends(require_admin)],
    service: Annotated[MaterialService, Depends(get_material_service)],
    difficulty: Annotated[DifficultyLevel, Form()] = "medium",
    file: UploadFile = File(...),
) -> MaterialResponse:
    """Upload a `.md` or `.txt` study file (max 2 MB) as a new study material (admin only)."""
    return await service.upload_material(
        file=file,
        title=title,
        subject=subject,
        topic=topic,
        difficulty=difficulty,
        user_id=current_user.id,
    )


@router.get("/{material_id}", response_model=MaterialResponse, status_code=status.HTTP_200_OK)
async def get_material(
    material_id: int,
    service: Annotated[MaterialService, Depends(get_material_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> MaterialResponse:
    """Fetch a single study material by ID (raises HTTP 404 if missing)."""
    return await service.get_by_id(material_id)


@router.patch("/{material_id}", response_model=MaterialResponse, status_code=status.HTTP_200_OK)
async def update_material(
    material_id: int,
    payload: MaterialUpdate,
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[MaterialService, Depends(get_material_service)],
) -> MaterialResponse:
    """Partially update a study material and re-embed chunks if text changed (admin only)."""
    return await service.update_material(material_id, payload)


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id: int,
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[MaterialService, Depends(get_material_service)],
) -> None:
    """Delete a study material and cascade-delete all of its vector chunks (admin only)."""
    await service.delete_material(material_id)


@router.post("/{material_id}/ingest", response_model=IngestResponse, status_code=status.HTTP_200_OK)
async def reingest_material(
    material_id: int,
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[MaterialService, Depends(get_material_service)],
) -> IngestResponse:
    """Rebuild vector embeddings for an existing material (admin only)."""
    return await service.reingest_material(material_id)
