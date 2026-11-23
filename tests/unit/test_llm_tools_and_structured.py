"""Unit tests for LLM tool schemas, closure isolation, JSON fence stripping, and math utils."""

import json
from types import SimpleNamespace
from typing import Any

import pytest
from google.genai import types
from google.genai.errors import APIError as GeminiAPIError
from starlette.requests import Request

from app.core.exceptions import gemini_exception_handler
from app.core.utils import average_percentage, calculate_percentage
from app.integrations import embedding as embedding_mod
from app.integrations.llm.chat import _build_contents, _execute_tool_calls
from app.integrations.llm.structured import strip_markdown_fences
from app.integrations.llm.tools import GenerateQuizArgs, ToolSpec, build_function_declaration


def test_function_declaration_exposes_only_safe_args():
    async def _noop(args: GenerateQuizArgs) -> dict[str, Any]:
        return {}

    spec = ToolSpec(
        name="generate_practice_quiz",
        description="Create quiz",
        args_schema=GenerateQuizArgs,
        handler=_noop,
    )
    decl = build_function_declaration(spec)
    props = decl.parameters_json_schema["properties"]
    assert set(props.keys()) == {"subject", "topic", "difficulty", "num_questions", "question_type"}
    assert "user_id" not in props
    assert "quiz_service" not in props


@pytest.mark.asyncio
async def test_execute_tool_calls_blocks_user_override_and_sanitizes_errors():
    bound_user_id = 99

    async def _handler(args: GenerateQuizArgs) -> dict[str, Any]:
        return {"user_id": bound_user_id, "num_questions": args.num_questions}

    async def _failing(args: GenerateQuizArgs) -> dict[str, Any]:
        raise RuntimeError("SECRET_SQL_ERROR: password=leaked")

    tool_map = {
        "generate_practice_quiz": ToolSpec("generate_practice_quiz", "Create", GenerateQuizArgs, _handler),
        "broken_tool": ToolSpec("broken_tool", "Broken", GenerateQuizArgs, _failing),
    }

    class _FakeFC:
        def __init__(self, name: str, args: dict[str, Any]):
            self.name = name
            self.args = args

    calls = [
        # Even if prompt-injected args include `user_id=1`, `extra="ignore"` + closure preserve `99`
        _FakeFC("generate_practice_quiz", {"subject": "math", "topic": "algebra", "num_questions": "3", "user_id": 1}),
        _FakeFC("broken_tool", {"subject": "math", "topic": "algebra"}),
    ]
    executed, _ = await _execute_tool_calls(calls, tool_map)
    assert executed[0]["result"] == {"user_id": 99, "num_questions": 3}
    assert executed[1]["result"] == {"status": "error", "message": "Tool execution failed."}
    assert "SECRET_SQL_ERROR" not in str(executed[1])


def test_strip_markdown_fences_and_percentage_helpers():
    fenced = '```json\n{"score": 10}\n```'
    assert strip_markdown_fences(fenced) == '{"score": 10}'
    assert calculate_percentage(3, 4) == 75.0
    assert calculate_percentage(1, 0) == 0.0
    assert average_percentage([(3, 4), (1, 4)]) == 50.0
    assert average_percentage([]) == 0.0


def test_build_contents_signals_missing_rag_context():
    contents = _build_contents([], "What is tungsten?", rag_context=None)
    assert "No relevant study materials were found" in contents[-1].parts[0].text


@pytest.mark.asyncio
async def test_embedding_service_wraps_chunks_in_content_and_uses_configured_version(monkeypatch):
    called_versions: list[str | None] = []
    calls: list[tuple[Any, Any]] = []

    class _FakeModels:
        async def embed_content(self, *, model: str, contents: Any, config: Any) -> Any:
            calls.append((contents, config))
            return SimpleNamespace(embeddings=[SimpleNamespace(values=[3.0, 4.0]) for _ in contents])

    fake_client = SimpleNamespace(aio=SimpleNamespace(models=_FakeModels()))

    def _fake_get_client(api_version: str | None = None) -> Any:
        called_versions.append(api_version)
        return fake_client

    monkeypatch.setattr(embedding_mod, "get_gemini_client", _fake_get_client)
    svc = embedding_mod.EmbeddingService()

    vecs = await svc.embed_texts(["chunk one", "chunk two"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 384
    assert vecs[0][:3] == pytest.approx([0.6, 0.8, 0.0])
    assert called_versions == [None]
    assert len(calls[0][0]) == 2
    assert all(isinstance(item, types.Content) for item in calls[0][0])
    assert calls[0][1].task_type == "RETRIEVAL_DOCUMENT"

    qvec = await svc.embed_query("search question")
    assert len(qvec) == 384
    assert qvec[:3] == pytest.approx([0.6, 0.8, 0.0])
    assert calls[1][1].task_type == "RETRIEVAL_QUERY"


@pytest.mark.asyncio
async def test_gemini_exception_handler_maps_status_codes_safely():
    req = Request({"type": "http", "method": "POST", "path": "/api/v1/chat", "headers": []})
    cases = [
        (429, 429, "ai_rate_limited"),
        (503, 503, "ai_unavailable"),
        (404, 502, "ai_upstream_error"),
    ]
    for upstream, expected_status, expected_slug in cases:
        exc = GeminiAPIError(upstream, {"error": {"status": "ERR", "message": "secret-upstream-detail"}})
        resp = await gemini_exception_handler(req, exc)
        payload = json.loads(bytes(resp.body))
        assert resp.status_code == expected_status
        assert payload["error"] == expected_slug
        assert payload["details"] == {"upstream_status": upstream}
        assert "secret-upstream-detail" not in payload["message"]
