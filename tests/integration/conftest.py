"""Fixtures for live integration tests with automatic API teardown cleanup."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ["ENVIRONMENT"] = "testing"

from app.main import app  # noqa: E402
from tests.integration.helpers import api  # noqa: E402


@pytest.fixture(scope="function")
async def admin_token() -> str:
    """Log in as seeded admin and return the JWT access token."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@omnitest.com", "password": "AdminPass123!"},
        )
        assert r.status_code == 200, f"Admin login failed: {r.text}"
        return r.json()["access_token"]


@pytest.fixture(scope="function")
async def student_token() -> str:
    """Log in as seeded student and return the JWT access token."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "student@omnitest.com", "password": "StudentPass123!"},
        )
        assert r.status_code == 200, f"Student login failed: {r.text}"
        return r.json()["access_token"]


@pytest.fixture(scope="function")
async def admin_headers(admin_token: str) -> dict[str, str]:
    """Return Authorization header with admin Bearer token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
async def student_headers(student_token: str) -> dict[str, str]:
    """Return Authorization header with student Bearer token."""
    return {"Authorization": f"Bearer {student_token}"}


@pytest.fixture(scope="function")
async def material_id(admin_headers: dict[str, str]):
    """Create a temporary study material and delete it after the test finishes."""
    r = await api(
        "post",
        "/api/v1/materials",
        headers=admin_headers,
        json={
            "title": "Fixture Material",
            "subject": "science",
            "topic": "biology",
            "difficulty": "easy",
            "content": "Photosynthesis is the process by which plants convert sunlight into energy. " * 3,
            "source": "fixture",
        },
    )
    assert r.status_code == 201, f"Fixture material creation failed: {r.text}"
    created_id = r.json()["id"]
    yield created_id
    await api("delete", f"/api/v1/materials/{created_id}", headers=admin_headers)


@pytest.fixture(scope="function")
async def quiz_id(admin_headers: dict[str, str]):
    """Create a temporary quiz and delete it after the test finishes."""
    r = await api(
        "post",
        "/api/v1/quizzes",
        headers=admin_headers,
        json={
            "title": "Fixture Quiz",
            "subject": "math",
            "topic": "arithmetic",
            "difficulty": "easy",
            "questions": [
                {
                    "type": "mcq",
                    "prompt": "What is 2 + 2?",
                    "options": ["A. 3", "B. 4", "C. 5", "D. 6"],
                    "correct_answer": "B",
                    "explanation": "2 + 2 = 4",
                    "order_num": 1,
                }
            ],
        },
    )
    assert r.status_code == 201, f"Fixture quiz creation failed: {r.text}"
    created_id = r.json()["id"]
    yield created_id
    await api("delete", f"/api/v1/quizzes/{created_id}", headers=admin_headers)
