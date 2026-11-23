"""Validation helper for `.md` / `.txt` study material file uploads."""

from pathlib import Path

from fastapi import UploadFile
from pydantic import ValidationError as PydanticValidationError

from app.core.constants import ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_BYTES
from app.core.exceptions import ValidationError
from app.modules.materials.schemas import MaterialCreate


async def parse_uploaded_material(
    file: UploadFile,
    title: str,
    subject: str,
    topic: str,
    difficulty: str,
) -> MaterialCreate:
    """Validate uploaded extension, 2 MB size cap, UTF-8 text, and DTO fields."""
    raw_name = Path(file.filename or "upload.txt").name
    if Path(raw_name).suffix.lower() not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValidationError("Only .md and .txt files are supported for material upload")

    content_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content_bytes) > MAX_UPLOAD_BYTES:
        raise ValidationError("Uploaded file exceeds the 2 MB limit")

    content_text = content_bytes.decode("utf-8", errors="replace").strip()
    try:
        return MaterialCreate(
            title=title,
            subject=subject,
            topic=topic,
            difficulty=difficulty,  # type: ignore[arg-type]
            content=content_text,
            source=raw_name[:255],
        )
    except PydanticValidationError as exc:
        raise ValidationError("Invalid uploaded study material fields", details={"errors": exc.errors()}) from None
