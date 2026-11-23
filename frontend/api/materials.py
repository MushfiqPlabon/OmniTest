"""Frontend HTTP client helpers for study materials and RAG ingestion."""

from __future__ import annotations

from typing import Any

from api.http import APITransport, build_params


class MaterialsAPI:
    """Wraps `/materials` CRUD, file upload, and embedding re-ingestion endpoints."""

    def __init__(self, transport: APITransport):
        self._http = transport

    def list(
        self,
        token: str,
        subject: str | None = None,
        topic: str | None = None,
        difficulty: str | None = None,
        search: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        """Fetch paginated study materials matching optional filters."""
        params = build_params(page=page, size=size, subject=subject, topic=topic, difficulty=difficulty, search=search)
        return self._http.request("GET", "/materials", token=token, params=params)

    def create(self, token: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create and chunk-embed a new study material (admin only)."""
        return self._http.request("POST", "/materials", token=token, json=data, timeout=60.0)

    def update(self, token: str, material_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Partially update study material metadata or text content (admin only)."""
        return self._http.request("PATCH", f"/materials/{material_id}", token=token, json=data, timeout=60.0)

    def delete(self, token: str, material_id: int) -> None:
        """Delete a study material and its vector chunks (admin only)."""
        self._http.request("DELETE", f"/materials/{material_id}", token=token)

    def reingest(self, token: str, material_id: int) -> dict[str, Any]:
        """Re-split and re-embed an existing study material (admin only)."""
        return self._http.request("POST", f"/materials/{material_id}/ingest", token=token, timeout=120.0)

    def upload(
        self,
        token: str,
        title: str,
        subject: str,
        topic: str,
        difficulty: str,
        filename: str,
        file_bytes: bytes,
    ) -> dict[str, Any]:
        """Upload a `.md` or `.txt` study file via multipart form data (admin only)."""
        form_data = {"title": title, "subject": subject, "topic": topic, "difficulty": difficulty}
        files = {"file": (filename, file_bytes)}
        return self._http.request("POST", "/materials/upload", token=token, data=form_data, files=files, timeout=120.0)
