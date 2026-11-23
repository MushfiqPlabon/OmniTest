"""Password hashing (Argon2id) and JWT authentication utilities.

Security properties:
- `verify_password_async` runs Argon2id against a precomputed dummy hash when
  the account does not exist, preventing timing-based email enumeration.
- `validate_password_byte_length` caps passwords at 72 UTF-8 bytes to block hashing DoS.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

_password_hash = PasswordHash((Argon2Hasher(),))
_DUMMY_HASH = _password_hash.hash("omnitest-dummy-timing-guard")


def validate_password_byte_length(password: str) -> str:
    """Enforce a 72 UTF-8 byte ceiling on passwords so hashing cannot be DoS-abused."""
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes in UTF-8")
    return password


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    try:
        return _password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False


async def hash_password_async(password: str) -> str:
    """Hash a password off the asyncio event loop."""
    return await asyncio.to_thread(hash_password, password)


async def verify_password_async(plain_password: str, hashed_password: str | None) -> bool:
    """Verify a password off the event loop in constant time even when user is missing."""
    if hashed_password is None:
        await asyncio.to_thread(verify_password, plain_password, _DUMMY_HASH)
        return False
    return await asyncio.to_thread(verify_password, plain_password, hashed_password)


def create_access_token(
    subject: str | int,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token with an expiration timestamp."""
    now = datetime.now(UTC)
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = now + delta

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        to_encode.update(extra_claims)

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token, raising UnauthorizedError on failure."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token has expired") from None
    except jwt.InvalidTokenError:
        raise UnauthorizedError("Invalid token") from None
