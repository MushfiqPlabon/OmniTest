"""Async database queries for users and roles (`AuthRepository`).

Why SQL lives here instead of `services.py`:
Keeping SQLAlchemy `select()` statements isolated in repositories makes business
logic easier to read and keeps DB access consistent across all modules.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Role, User


class AuthRepository:
    """Encapsulates all user and role database reads/writes."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> User | None:
        """Look up a user case-insensitively by email, returning `None` if absent."""
        # Normalize email at query time so `"User@Test.com"` matches `"user@test.com"`.
        stmt = select(User).where(User.email == email.strip().lower())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Fetch a user by numeric primary key (`sub` claim in JWT tokens)."""
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_role_by_name(self, name: str) -> Role | None:
        """Fetch a `Role` record by name (for example `"student"` or `"admin"`)."""
        stmt = select(Role).where(Role.name == name)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_user(self, email: str, password_hash: str, full_name: str, role_id: int) -> User:
        """Insert a new user row, commit immediately, and refresh DB-generated fields (`id`, timestamps)."""
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role_id=role_id,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
