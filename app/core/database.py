"""Async PostgreSQL database connection setup.

Creates four building blocks shared across the backend:
1. `engine`: manages PostgreSQL connections using `asyncpg`.
2. `AsyncSessionLocal`: opens fresh async database sessions on demand.
3. `Base`: declarative base class inherited by all SQLAlchemy ORM models.
4. `get_db_session()`: FastAPI dependency providing one request-scoped session.
"""

import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Pytest opens a fresh asyncio event loop per test; NullPool avoids cross-loop errors.
engine_kwargs: dict[str, Any] = {
    "echo": settings.LOG_LEVEL.upper() == "DEBUG",
    "future": True,
}
if os.getenv("ENVIRONMENT") == "testing" or settings.ENVIRONMENT == "testing":
    engine_kwargs["poolclass"] = NullPool
else:
    # Recycle idle connections every 4 minutes and ping before checkout on cloud Postgres.
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 240

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Typed SQLAlchemy 2.0 declarative base inherited by all ORM tables."""


def utc_now() -> datetime:
    """Return the current UTC timestamp for SQLAlchemy column defaults."""
    return datetime.now(UTC)


async def release_transaction(session: AsyncSession) -> None:
    """Close any open read transaction before a slow external AI network call."""
    if session.in_transaction():
        await session.rollback()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield one async database session per HTTP request and roll back on errors."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
