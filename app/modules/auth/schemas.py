"""Pydantic schemas for registration, login, JWT responses, and user profiles.

Every incoming auth request normalizes email casing and checks password length
before `AuthService` hashes or touches the database.
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from app.core.security import validate_password_byte_length


class _CredentialsBase(BaseModel):
    """Shared email normalization and 72-byte password check for auth payloads."""

    email: EmailStr
    password: str

    @field_validator("email", mode="after")
    @classmethod
    def _normalize_email(cls, value: EmailStr) -> str:
        """Store and match emails in lowercase."""
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def _check_password_bytes(cls, value: str) -> str:
        """Reject passwords exceeding 72 UTF-8 bytes."""
        return validate_password_byte_length(value)


class RegisterRequest(_CredentialsBase):
    """Payload validated when registering a new student account."""

    password: str = Field(..., min_length=6, description="User password (max 72 UTF-8 bytes)")
    full_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]


class LoginRequest(_CredentialsBase):
    """Credentials sent to `/api/v1/auth/login`."""

    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """JWT Bearer token bundle returned on successful registration or login."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    role: str
    email: EmailStr


class UserResponse(BaseModel):
    """Safe public user profile (never exposes `password_hash`)."""

    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
