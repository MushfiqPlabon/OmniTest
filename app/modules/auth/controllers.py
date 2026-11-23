"""HTTP route handlers for user registration, login, and profile inspection.

Mounted under `/api/v1/auth`. Controllers stay intentionally thin: FastAPI
validates JSON bodies via Pydantic schemas and passes `Depends(...)` services
into the handler, which delegates business rules to `AuthService`.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import get_auth_service, get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.modules.auth.services import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Create a new student account and immediately return a signed JWT access token."""
    return await service.register(payload)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Verify email + password and return a fresh JWT access token."""
    return await service.login(payload)


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_me(
    # `get_current_user` reads the `Authorization: Bearer <token>` header automatically
    # and raises 401 before this handler even runs if the token is missing or invalid.
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Return the logged-in user's public profile from their Bearer token."""
    return await service.get_me(current_user)
