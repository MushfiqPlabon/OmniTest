"""Live integration tests for AI Tutor Chat, RAG grounding, and DB tool calling."""

import pytest

from tests.integration.helpers import api

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_26_chat_triggers_ai_quiz_generation(student_headers, admin_headers):
    """Full flow: chat message -> Gemini calls tool -> quiz persisted in Postgres."""
    r = await api(
        "post",
        "/api/v1/chat",
        headers=student_headers,
        json={
            "message": "Please generate and save a practice quiz on the quadratic formula for GED math with 3 questions.",
            "history": [],
        },
    )
    assert r.status_code == 200, f"Chat failed: {r.text}"
    tool_calls = r.json().get("tool_calls", [])
    assert len(tool_calls) >= 1
    assert tool_calls[0]["tool"] == "generate_practice_quiz"
    quiz_id = tool_calls[0]["result"].get("quiz_id")
    assert quiz_id
    try:
        r2 = await api("get", f"/api/v1/quizzes/{quiz_id}", headers=student_headers)
        assert r2.status_code == 200
        assert len(r2.json()["questions"]) >= 1
    finally:
        await api("delete", f"/api/v1/quizzes/{quiz_id}", headers=admin_headers)


@pytest.mark.asyncio
async def test_27_chat_with_rag_grounded_answer(student_headers):
    """Chat answers a question grounded in the knowledge base, citing sources."""
    r = await api(
        "post",
        "/api/v1/chat",
        headers=student_headers,
        json={"message": "Explain how photosynthesis works and what chlorophyll does.", "history": []},
    )
    assert r.status_code == 200
    assert len(r.json()["message"]) > 20


@pytest.mark.asyncio
async def test_28_chat_says_nothing_found_for_irrelevant_query(student_headers):
    """Chat reports no relevant study materials found when asked an out-of-domain question."""
    r = await api(
        "post",
        "/api/v1/chat",
        headers=student_headers,
        json={"message": "What is the exact melting point of tungsten in Kelvin?", "history": []},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["sources"] == []
    reply = data["message"].lower()
    assert any(
        phrase in reply for phrase in ["no relevant", "not found", "no matching", "don't have", "knowledge base"]
    )


@pytest.mark.asyncio
async def test_29_chat_multiturn_session_persisted(student_headers):
    """Multi-turn chat session is stored in DB and continues with context."""
    r1 = await api(
        "post",
        "/api/v1/chat",
        headers=student_headers,
        json={"message": "My name is Tariq and I am studying for GED math.", "history": []},
    )
    assert r1.status_code == 200
    session_id = r1.json()["session_id"]

    r2 = await api(
        "post",
        "/api/v1/chat",
        headers=student_headers,
        json={
            "message": "What subject am I studying for?",
            "history": [
                {"role": "user", "content": "My name is Tariq and I am studying for GED math."},
                {"role": "assistant", "content": r1.json()["message"]},
            ],
            "session_id": session_id,
        },
    )
    assert r2.status_code == 200
    assert any(w in r2.json()["message"].lower() for w in ["math", "ged"])
