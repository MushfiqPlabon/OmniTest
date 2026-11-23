"""Live infrastructure, PostgreSQL/pgvector, and Gemini API smoke tests."""

import math

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.integrations.embedding import embedding_service
from app.integrations.llm import ToolSpec, chat_with_tools
from app.integrations.llm.tools import GenerateQuizArgs
from tests.integration.helpers import api

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_01_database_connection_and_pgvector():
    """Real Postgres: connects, pgvector extension is active."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.connect() as conn:
        assert await conn.scalar(text("SELECT 1")) == 1
        ext = await conn.scalar(text("SELECT extname FROM pg_extension WHERE extname='vector'"))
        assert ext == "vector", "pgvector must be installed — run: alembic upgrade head"
    await engine.dispose()


@pytest.mark.asyncio
async def test_02_health_endpoint():
    """GET /health -> 200 with correct service name."""
    r = await api("get", "/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"
    assert r.json()["service"] == "omnitest"


@pytest.mark.asyncio
async def test_03_gemini_generates_text():
    """Gemini API key is valid and model responds."""
    reply, tool_calls = await chat_with_tools(
        message="What is the standard slope-intercept form of a line?",
        history=[],
        rag_context="Linear equations: the slope-intercept form is y = mx + b, where m is slope and b is the y-intercept.",
        tools=[],
    )
    assert any(w in reply.lower() for w in ["y = mx + b", "slope", "intercept"]), f"Unexpected reply: {reply}"
    assert tool_calls == []


@pytest.mark.asyncio
async def test_04_gemini_multiturn_history():
    """Gemini remembers conversation history across turns."""
    history = [
        {"role": "user", "content": "I am studying for the GED Math exam."},
        {"role": "assistant", "content": "GED Math covers algebra, geometry, and arithmetic. How can I help?"},
    ]
    reply, _ = await chat_with_tools(
        message="Which exam did I say I am preparing for?",
        history=history,
        rag_context="GED Math covers algebraic and quantitative reasoning.",
        tools=[],
    )
    assert "ged" in reply.lower(), f"Model should recall GED from history, got: {reply}"


@pytest.mark.asyncio
async def test_05_gemini_tool_calling_fires():
    """Gemini decides to call generate_practice_quiz when asked."""
    fired: dict[str, str] = {}

    async def _run_quiz(args: GenerateQuizArgs):
        fired["subject"] = args.subject
        fired["topic"] = args.topic
        return {"status": "success", "quiz_id": 999, "title": f"Quiz on {args.topic}", "questions_count": 3}

    spec = ToolSpec(
        name="generate_practice_quiz",
        description="Generate and save a practice quiz for a student",
        args_schema=GenerateQuizArgs,
        handler=_run_quiz,
    )
    reply, tool_calls = await chat_with_tools(
        message="Please generate and save a practice quiz on algebra for GED math with 3 questions.",
        history=[],
        rag_context=None,
        tools=[spec],
    )
    assert fired.get("subject"), f"Tool was not called. Reply: {reply}"
    assert any(tc["tool"] == "generate_practice_quiz" for tc in tool_calls)


@pytest.mark.asyncio
async def test_06_gemini_embedding_shape_and_norm():
    """Gemini embedding returns 384-dimensional normalized vector."""
    vecs = await embedding_service.embed_texts(["The quadratic formula solves ax^2+bx+c=0"])
    assert len(vecs) == 1
    vec = vecs[0]
    assert len(vec) == 384
    norm = math.sqrt(sum(x * x for x in vec))
    assert 0.98 <= norm <= 1.02
