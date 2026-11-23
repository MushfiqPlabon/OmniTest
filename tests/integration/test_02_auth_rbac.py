"""Live integration tests for authentication and RBAC endpoints."""

import pytest

from tests.integration.helpers import api

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_07_register_new_student():
    """POST /auth/register -> 201 or 409 (already exists)."""
    r = await api(
        "post",
        "/api/v1/auth/register",
        json={"email": "testrunner@omnitest.com", "password": "TestRunner123!", "full_name": "Test Runner"},
    )
    assert r.status_code in (201, 409), f"Unexpected: {r.status_code} {r.text}"


@pytest.mark.asyncio
async def test_08_login_admin(admin_token):
    """POST /auth/login -> JWT for admin."""
    assert admin_token


@pytest.mark.asyncio
async def test_09_login_student(student_token):
    """POST /auth/login -> JWT for student."""
    assert student_token


@pytest.mark.asyncio
async def test_10_wrong_password_same_error():
    """Wrong email and wrong password return identical 401 — no user enumeration."""
    r_bad_pw = await api(
        "post", "/api/v1/auth/login", json={"email": "admin@omnitest.com", "password": "WrongPassword!"}
    )
    r_bad_email = await api("post", "/api/v1/auth/login", json={"email": "nobody@nowhere.com", "password": "Whatever!"})
    assert r_bad_pw.status_code == 401
    assert r_bad_email.status_code == 401
    assert r_bad_pw.json()["message"] == r_bad_email.json()["message"]


@pytest.mark.asyncio
async def test_11_get_me_returns_correct_role(admin_headers):
    """GET /auth/me -> returns user profile with role from DB."""
    r = await api("get", "/api/v1/auth/me", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "admin@omnitest.com"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_12_no_token_returns_401():
    """Protected routes require a JWT — no token = 401."""
    for path in ["/api/v1/auth/me", "/api/v1/materials", "/api/v1/quizzes"]:
        r = await api("get", path)
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_13_tampered_token_rejected():
    """Tampered JWT -> 401."""
    r = await api("get", "/api/v1/auth/me", headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.fake.payload"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_14_student_cannot_write_domain(student_headers):
    """Student attempting admin-only write -> 403 Forbidden."""
    r = await api(
        "post",
        "/api/v1/materials",
        headers=student_headers,
        json={
            "title": "Should Fail",
            "subject": "math",
            "topic": "test",
            "difficulty": "easy",
            "content": "Student should not be able to create materials.",
        },
    )
    assert r.status_code == 403
