"""Authentication business logic for signup, login, and user profiles.

When it runs: Called by `/api/v1/auth` routes (`/register`, `/login`, `/me`).
How & why: Hashes passwords off-loop with Argon2id, assigns the default
`student` role on signup, and runs dummy verification on unknown emails so
login timing stays uniform and returns the same `401` on wrong email or password.
"""

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import create_access_token, hash_password_async, verify_password_async
from app.modules.auth.models import User
from app.modules.auth.repositories import AuthRepository
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse


def _resolve_role_name(user: User) -> str:
    """Return user's role name with `'student'` fallback."""
    return user.role.name if user.role else "student"


def _ensure_valid_credentials(user: User | None, is_valid: bool) -> User:
    """Reject missing users, wrong passwords, or disabled accounts uniformly."""
    if user is None or not is_valid:
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise UnauthorizedError("Account is disabled")
    return user


class AuthService:
    """Coordinates password hashing, JWT creation, and role checks with `AuthRepository`."""

    def __init__(self, repo: AuthRepository):
        self.repo = repo

    def _build_token_response(self, user: User, role_name: str) -> TokenResponse:
        """Sign a JWT containing user ID, email, and role and wrap it in `TokenResponse`."""
        token = create_access_token(subject=user.id, extra_claims={"email": user.email, "role": role_name})
        return TokenResponse(access_token=token, token_type="bearer", role=role_name, email=user.email)

    async def register(self, req: RegisterRequest) -> TokenResponse:
        """Register a new student account, rejecting duplicate emails with HTTP 409 Conflict."""
        if await self.repo.get_user_by_email(req.email):
            raise ConflictError("User with this email already exists")

        role = await self.repo.get_role_by_name("student")
        if not role:
            raise NotFoundError("Default 'student' role not configured in database")

        pw_hash = await hash_password_async(req.password)
        try:
            user = await self.repo.create_user(
                email=req.email,
                password_hash=pw_hash,
                full_name=req.full_name,
                role_id=role.id,
            )
        except IntegrityError:
            await self.repo.session.rollback()
            raise ConflictError("User with this email already exists") from None
        return self._build_token_response(user, role.name)

    async def login(self, req: LoginRequest) -> TokenResponse:
        """Authenticate email + password in constant time and issue a Bearer token."""
        user = await self.repo.get_user_by_email(req.email)
        stored_hash = user.password_hash if user else None
        is_valid = await verify_password_async(req.password, stored_hash)
        active_user = _ensure_valid_credentials(user, is_valid)
        return self._build_token_response(active_user, _resolve_role_name(active_user))

    async def get_me(self, current_user: User) -> UserResponse:
        """Convert the authenticated `User` ORM row into a safe API response."""
        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            role=_resolve_role_name(current_user),
            is_active=current_user.is_active,
            created_at=current_user.created_at,
        )
