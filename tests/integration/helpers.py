"""Shared test environment bootstrap and HTTP transport helpers for live integration tests."""

import os

from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient

# Load real .env before importing any app module
load_dotenv(override=True)
os.environ["ENVIRONMENT"] = "testing"

from app.main import app  # noqa: E402


async def api(method: str, path: str, **kwargs):
    """Thin async wrapper so integration tests share one ASGI transport."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await getattr(client, method)(path, **kwargs)
