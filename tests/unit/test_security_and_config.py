"""Unit tests for password hashing, timing guard, JWTs, URLs, and config validation."""

from datetime import timedelta

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password_async,
    validate_password_byte_length,
    verify_password_async,
)
from app.core.urls import normalize_async_database_url
from app.modules.auth.schemas import LoginRequest, RegisterRequest


@pytest.mark.asyncio
async def test_argon2_hash_and_constant_time_missing_user():
    pw_hash = await hash_password_async("StrongPass123!")
    assert pw_hash.startswith("$argon2")
    assert await verify_password_async("StrongPass123!", pw_hash) is True
    assert await verify_password_async("WrongPass!", pw_hash) is False
    # Missing user (`stored_hash=None`) still returns False cleanly via dummy verification
    assert await verify_password_async("AnyPass!", None) is False


def test_password_72_byte_cap_on_register_and_login():
    long_pw = "a" * 73
    with pytest.raises(ValueError, match="72 bytes"):
        validate_password_byte_length(long_pw)

    with pytest.raises(ValidationError):
        RegisterRequest(email="u@example.com", password=long_pw, full_name="Test User")

    with pytest.raises(ValidationError):
        LoginRequest(email="u@example.com", password=long_pw)


def test_jwt_create_decode_and_expiry():
    token = create_access_token(subject=42, extra_claims={"role": "student"})
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "student"

    expired = create_access_token(subject=42, expires_delta=timedelta(seconds=-5))
    with pytest.raises(UnauthorizedError, match="expired"):
        decode_access_token(expired)


def test_normalize_async_database_url():
    raw = "postgres://user:pass@host:5432/db?sslmode=require"
    normalized = normalize_async_database_url(raw)
    assert normalized == "postgresql+asyncpg://user:pass@host:5432/db?ssl=require"


def test_production_requires_32_char_secret_key():
    with pytest.raises(ValidationError, match="32 characters"):
        Settings(
            _env_file=None,
            SECRET_KEY="too-short-for-prod-16",
            GEMINI_API_KEY="dummy",
            ENVIRONMENT="production",
        )
