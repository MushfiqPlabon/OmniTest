"""Shared async CRUD base repository for SQLAlchemy ORM models.

Why this exists:
Eliminates repeated create/get/list/update/delete boilerplate across feature
modules while keeping SQL isolated in repository classes.
"""

from collections.abc import Sequence
from typing import Any

from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError


class BaseRepository:
    """Shared async CRUD, filtering, and pagination operations for ORM models."""

    model: type[Any]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: Any) -> Any:
        """Persist a new row and refresh database-generated defaults."""
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def get_by_id(self, entity_id: int, options: Sequence[Any] = ()) -> Any | None:
        """Return one row by primary key ID, or `None` if absent."""
        stmt = select(self.model).where(self.model.id == entity_id)
        if options:
            stmt = stmt.options(*options)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_or_404(self, entity_id: int, label: str = "Resource", options: Sequence[Any] = ()) -> Any:
        """Return one row by ID or raise `NotFoundError` (HTTP 404)."""
        entity = await self.get_by_id(entity_id, options=options)
        if not entity:
            raise NotFoundError(f"{label} with id {entity_id} not found")
        return entity

    async def list_filtered(
        self,
        *,
        filters: Filter | None = None,
        params: Params | None = None,
        schema: type[BaseModel] | None = None,
    ) -> Page[Any]:
        """Return a deterministically ordered page of rows matching optional filters."""
        stmt = select(self.model).order_by(self.model.id.desc())
        if filters is not None:
            stmt = filters.filter(stmt)

        page_params = params or Params(page=1, size=20)
        transformer = None
        if schema is not None:

            def _to_schema(items: Sequence[Any]) -> list[Any]:
                return [schema.model_validate(item) for item in items]

            transformer = _to_schema
        return await apaginate(self.session, stmt, params=page_params, transformer=transformer)

    async def update(self, entity: Any, update_data: dict[str, Any]) -> Any:
        """Apply explicit PATCH fields (including nullable `None` clears) and commit."""
        for key, value in update_data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: Any) -> None:
        """Delete an entity row and commit the transaction."""
        await self.session.delete(entity)
        await self.session.commit()
