"""FastAPI authentication and role guards injected via `Depends()`.

When it runs: On every protected route handler before endpoint logic runs.
How & why: Decodes the Bearer JWT, reloads the active user and DB role per
request so deactivated accounts lose access immediately, and lets
`require_role` build reusable role dependencies like `require_admin`.
"""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.modules.auth.models import User
from app.modules.auth.repositories import AuthRepository
from app.modules.auth.services import AuthService

# `auto_error=False` lets us raise `UnauthorizedError` so errors use `ErrorResponse` JSON.
security_bearer = HTTPBearer(auto_error=False)


def get_auth_repo(session: AsyncSession = Depends(get_db_session)) -> AuthRepository:
    """Provide an `AuthRepository` bound to the active request's DB session."""
    return AuthRepository(session)


def get_auth_service(repo: AuthRepository = Depends(get_auth_repo)) -> AuthService:
    """Provide an `AuthService` wired with `AuthRepository`."""
    return AuthService(repo)


def _extract_user_id(credentials: HTTPAuthorizationCredentials | None) -> int:
    """Decode Bearer JWT and parse its numeric `sub` user ID."""
    if not credentials:
        raise UnauthorizedError("Authentication token is required")
    payload = decode_access_token(credentials.credentials)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError("Invalid token payload")
    try:
        return int(user_id_str)
    except (TypeError, ValueError):
        raise UnauthorizedError("Invalid token subject") from None


def _require_active_user(user: User | None) -> User:
    """Ensure the looked-up user exists and is active."""
    if not user:
        raise UnauthorizedError("User no longer exists")
    if not user.is_active:
        raise UnauthorizedError("Account is inactive")
    return user


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_bearer)],
    repo: Annotated[AuthRepository, Depends(get_auth_repo)],
) -> User:
    """Validate the Bearer JWT and return the active database `User` row."""
    user_id = _extract_user_id(credentials)
    user = await repo.get_user_by_id(user_id)
    return _require_active_user(user)


def require_role(allowed_role: str) -> Callable[..., Any]:
    """Build a FastAPI dependency that enforces a specific database role."""

    async def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        """Reject users whose database role does not match `allowed_role` with HTTP 403."""
        role_name = current_user.role.name if current_user.role else ""
        if role_name != allowed_role:
            raise ForbiddenError(f"Access forbidden: requires '{allowed_role}' role")
        return current_user

    return role_checker


require_admin = require_role("admin")
