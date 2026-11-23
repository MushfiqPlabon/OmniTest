"""Live integration tests for Essays AI grading, FastMCP HTTP/stdio, and error handling."""

import pytest

from tests.integration.helpers import api

pytestmark = pytest.mark.integration

_STRUCTURED_RUBRIC = {
    "max_score": 12,
    "criteria": [
        {"name": "Argument Development", "max": 3, "desc": "Thesis and claim clarity"},
        {"name": "Evidence & Examples", "max": 3, "desc": "Supporting facts and reasoning"},
        {"name": "Organization", "max": 3, "desc": "Paragraph flow and transitions"},
        {"name": "Language & Style", "max": 3, "desc": "Grammar and academic tone"},
    ],
}


@pytest.mark.asyncio
async def test_30_admin_creates_essay_prompt(admin_headers):
    """POST /essays/prompts -> 201, essay prompt in DB (cleaned up after)."""
    r = await api(
        "post",
        "/api/v1/essays/prompts",
        headers=admin_headers,
        json={
            "subject": "writing",
            "topic": "argumentative",
            "prompt_text": "Should students be required to study a foreign language? Support your position.",
            "rubric": _STRUCTURED_RUBRIC,
            "difficulty": "medium",
        },
    )
    assert r.status_code == 201, r.text
    await api("delete", f"/api/v1/essays/prompts/{r.json()['id']}", headers=admin_headers)


@pytest.mark.asyncio
async def test_31_student_submits_essay_and_gets_ai_grading(student_headers, admin_headers):
    """POST /essays/prompts/{id}/submit -> Gemini grades against rubric and stores result."""
    r = await api(
        "post",
        "/api/v1/essays/prompts",
        headers=admin_headers,
        json={
            "subject": "writing",
            "topic": "argumentative",
            "prompt_text": "Should students be required to study a foreign language? Support your position.",
            "rubric": _STRUCTURED_RUBRIC,
            "difficulty": "medium",
        },
    )
    assert r.status_code == 201
    prompt_id = r.json()["id"]
    try:
        sub = await api(
            "post",
            f"/api/v1/essays/prompts/{prompt_id}/submit",
            headers=student_headers,
            json={
                "response_text": (
                    "Learning a foreign language broadens cultural understanding, improves cognitive flexibility, "
                    "and prepares students for global careers. Bilingual problem-solving complements STEM learning."
                )
            },
        )
        assert sub.status_code == 201, sub.text
        data = sub.json()
        assert 0 <= data["score"] <= data["max_score"]
        assert len(data["feedback"]) > 20
    finally:
        await api("delete", f"/api/v1/essays/prompts/{prompt_id}", headers=admin_headers)


@pytest.mark.asyncio
async def test_32_mcp_has_required_components():
    """FastMCP exposes 2+ tools, 1 prompt, and 1 resource template."""
    from app.mcp.server import mcp

    tools = await mcp.list_tools()
    prompts = await mcp.list_prompts()
    resources = await mcp.list_resource_templates()
    tool_names = [t.name for t in tools]
    assert "generate_practice_quiz" in tool_names
    assert "search_study_materials" in tool_names
    assert len(prompts) >= 1
    assert len(resources) >= 1


@pytest.mark.asyncio
async def test_33_mcp_http_requires_auth_and_accepts_bearer(student_headers):
    """/mcp enforces 401 without Bearer auth and accepts authenticated MCP requests."""
    from app.main import app, lifespan

    async with lifespan(app):
        r_unauth = await api("post", "/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        assert r_unauth.status_code == 401

        r_auth = await api(
            "post",
            "/mcp",
            headers={**student_headers, "Accept": "application/json, text/event-stream"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            },
        )
        assert r_auth.status_code not in (401, 404)


@pytest.mark.asyncio
async def test_34_validation_error_422_clean():
    """Invalid request body -> 422 with structured error, no stack trace."""
    r = await api(
        "post",
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "123", "full_name": ""},
    )
    assert r.status_code == 422
    assert r.json()["error"] == "validation_error"
    assert "traceback" not in r.text.lower()


@pytest.mark.asyncio
async def test_35_conflict_409_on_duplicate_register():
    """Registering the same email twice -> 409 Conflict."""
    for _ in range(2):
        r = await api(
            "post",
            "/api/v1/auth/register",
            json={"email": "duplicate@omnitest.com", "password": "SomePass123!", "full_name": "Dup User"},
        )
    assert r.status_code == 409
    assert r.json()["error"] == "conflict"


@pytest.mark.asyncio
async def test_36_delete_material_204(admin_headers, material_id):
    """DELETE /materials/{id} -> 204 No Content, gone from DB."""
    r = await api("delete", f"/api/v1/materials/{material_id}", headers=admin_headers)
    assert r.status_code == 204
    r2 = await api("get", f"/api/v1/materials/{material_id}", headers=admin_headers)
    assert r2.status_code == 404
