"""Live integration tests for Quiz CRUD, `?search=`, grading, and attempt history."""

import pytest

from tests.integration.helpers import api

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_22_admin_creates_quiz(admin_headers):
    """POST /quizzes -> 201, quiz with questions in DB (cleaned up after)."""
    r = await api(
        "post",
        "/api/v1/quizzes",
        headers=admin_headers,
        json={
            "title": "Test: GED Math Basics",
            "subject": "math",
            "topic": "arithmetic",
            "difficulty": "easy",
            "questions": [
                {
                    "type": "mcq",
                    "prompt": "What is 15% of 200?",
                    "options": ["A. 25", "B. 30", "C. 35", "D. 40"],
                    "correct_answer": "B",
                    "explanation": "15% of 200 = 30",
                    "order_num": 1,
                }
            ],
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()
    try:
        assert len(data["questions"]) == 1
        assert "explanation" not in data["questions"][0]
    finally:
        await api("delete", f"/api/v1/quizzes/{data['id']}", headers=admin_headers)


@pytest.mark.asyncio
async def test_23_list_quizzes_with_filters_and_search(student_headers, quiz_id):
    """GET /quizzes?subject=math&difficulty=easy&search=Fixture -> filtered results."""
    r = await api(
        "get",
        "/api/v1/quizzes",
        headers=student_headers,
        params={"subject": "math", "difficulty": "easy", "search": "Fixture"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["total"] >= 1
    assert all(q["subject"] == "math" and q["difficulty"] == "easy" for q in data["items"])


@pytest.mark.asyncio
async def test_24_submit_quiz_attempt_and_score(admin_headers, student_headers):
    """POST /quizzes/{id}/attempt -> scored correctly against DB answers."""
    r = await api(
        "post",
        "/api/v1/quizzes",
        headers=admin_headers,
        json={
            "title": "Scoring Test Quiz",
            "subject": "math",
            "topic": "arithmetic",
            "difficulty": "easy",
            "questions": [
                {
                    "type": "mcq",
                    "prompt": "What is 15% of 200?",
                    "options": ["A. 25", "B. 30", "C. 35", "D. 40"],
                    "correct_answer": "B",
                    "explanation": "15% of 200 = 30",
                    "order_num": 1,
                },
                {
                    "type": "mcq",
                    "prompt": "Which is a prime number?",
                    "options": ["A. 9", "B. 15", "C. 17", "D. 21"],
                    "correct_answer": "C",
                    "explanation": "17 is prime",
                    "order_num": 2,
                },
            ],
        },
    )
    assert r.status_code == 201
    created_id = r.json()["id"]
    q1_id, q2_id = r.json()["questions"][0]["id"], r.json()["questions"][1]["id"]
    try:
        res = await api(
            "post",
            f"/api/v1/quizzes/{created_id}/attempt",
            headers=student_headers,
            json={"answers": {str(q1_id): "B", str(q2_id): "A"}},
        )
        assert res.status_code == 201, res.text
        data = res.json()
        assert data["score"] == 1
        assert data["max_score"] == 2
        assert data["percentage"] == 50.0
    finally:
        await api("delete", f"/api/v1/quizzes/{created_id}", headers=admin_headers)


@pytest.mark.asyncio
async def test_25_quiz_attempt_history_in_db(student_headers, admin_headers, quiz_id):
    """GET /quizzes/{id}/attempts and /quizzes/attempts/my -> persisted attempt returned."""
    quiz = (await api("get", f"/api/v1/quizzes/{quiz_id}", headers=student_headers)).json()
    q1_id = quiz["questions"][0]["id"]

    res = await api(
        "post",
        f"/api/v1/quizzes/{quiz_id}/attempt",
        headers=student_headers,
        json={"answers": {str(q1_id): "B"}},
    )
    assert res.status_code == 201

    attempts_r = await api("get", f"/api/v1/quizzes/{quiz_id}/attempts", headers=student_headers)
    assert attempts_r.status_code == 200
    assert len(attempts_r.json()) >= 1

    my_r = await api("get", "/api/v1/quizzes/attempts/my", headers=student_headers)
    assert my_r.status_code == 200
    assert any(a["quiz_id"] == quiz_id for a in my_r.json())
