"""Unit tests for `/mcp` Bearer authentication and API boundary validation."""

from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db_session
from app.core.security import create_access_token
from app.main import app
from app.mcp.auth import MCPBearerAuthMiddleware, current_mcp_user_id
from app.modules.auth.dependencies import get_current_user, require_admin


@pytest.mark.asyncio
async def test_mcp_rejects_missing_and_invalid_tokens():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r_no_auth = await client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        assert r_no_auth.status_code == 401
        assert r_no_auth.headers.get("www-authenticate") == "Bearer"
        assert r_no_auth.json()["error"] == "unauthorized"

        r_bad_auth = await client.post(
            "/mcp",
            headers={"Authorization": "Bearer fake.jwt.token"},
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize"},
        )
        assert r_bad_auth.status_code == 401
        assert r_bad_auth.json()["error"] == "unauthorized"


@pytest.mark.asyncio
async def test_mcp_bearer_middleware_sets_user_id_for_valid_token():
    observed_user_ids: list[int | None] = []

    async def _echo_app(scope, receive, send):
        observed_user_ids.append(current_mcp_user_id.get())
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    protected = MCPBearerAuthMiddleware(_echo_app)
    token = create_access_token(subject=77, extra_claims={"role": "student"})

    async with AsyncClient(transport=ASGITransport(app=protected), base_url="http://test") as client:
        resp = await client.post("/mcp", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert observed_user_ids == [77]
        assert current_mcp_user_id.get() is None


@pytest.mark.asyncio
async def test_pagination_bounds_and_upload_validation_return_422():
    fake_admin = SimpleNamespace(id=1, role=SimpleNamespace(name="admin"), is_active=True)

    async def _fake_db():
        yield None

    app.dependency_overrides[get_current_user] = lambda: fake_admin
    app.dependency_overrides[require_admin] = lambda: fake_admin
    app.dependency_overrides[get_db_session] = _fake_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r_page = await client.get("/api/v1/materials?page=0&size=500")
            assert r_page.status_code == 422
            assert r_page.json()["error"] == "validation_error"

            r_quiz_page = await client.get("/api/v1/quizzes?page=0")
            assert r_quiz_page.status_code == 422

            r_ext = await client.post(
                "/api/v1/materials/upload",
                data={"title": "Test", "subject": "math", "topic": "algebra", "difficulty": "easy"},
                files={"file": ("malware.exe", b"not allowed content")},
            )
            assert r_ext.status_code == 422
            assert r_ext.json()["error"] == "validation_error"

            r_bad_diff = await client.post(
                "/api/v1/materials/upload",
                data={"title": "Valid Title", "subject": "math", "topic": "algebra", "difficulty": "impossible"},
                files={"file": ("notes.md", b"Valid study notes content here.")},
            )
            assert r_bad_diff.status_code == 422
    finally:
        app.dependency_overrides.clear()
