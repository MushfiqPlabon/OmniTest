"""Idempotent database seed script safe to re-run on every container boot.

Ensures `student` and `admin` roles exist, optionally creates demo accounts
when `ENABLE_DEMO_ACCOUNTS=true`, and inserts starter study guides, quizzes,
and essay prompts without duplicating existing rows.
"""

import asyncio
import sys
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.modules.auth.models import Role, User
from app.modules.essays.models import EssayPrompt
from app.modules.materials.models import StudyMaterial
from app.modules.materials.repositories import MaterialRepository
from app.modules.materials.services import MaterialService
from app.modules.quizzes.models import Quiz
from scripts.data import MATERIALS_DATA, build_seed_prompts, build_seed_quizzes


async def _ensure_user(session: AsyncSession, email: str, password: str, full_name: str, role_id: int) -> User:
    """Create a seed account only if the email is missing."""
    res = await session.execute(select(User).where(User.email == email))
    user = res.scalars().first()
    if user:
        return user
    user = User(email=email, password_hash=hash_password(password), full_name=full_name, role_id=role_id)
    session.add(user)
    return user


async def _seed_roles_and_users(session: AsyncSession) -> int | None:
    """Ensure `student` and `admin` roles exist and optionally seed demo accounts."""
    role_rows = (await session.execute(select(Role))).scalars().all()
    existing_roles = {role.name: role for role in role_rows}
    for r_name in ("student", "admin"):
        if r_name not in existing_roles:
            role = Role(name=r_name, description=f"{r_name.capitalize()} account role")
            session.add(role)
            existing_roles[r_name] = role
    await session.flush()
    print("  [ok] Roles ready: student, admin")

    if not settings.ENABLE_DEMO_ACCOUNTS:
        print("  [skip] Demo accounts disabled (ENABLE_DEMO_ACCOUNTS=false)")
        return None

    admin_user = await _ensure_user(
        session, "admin@omnitest.com", "AdminPass123!", "OmniTest Administrator", existing_roles["admin"].id
    )
    await _ensure_user(
        session, "student@omnitest.com", "StudentPass123!", "GED SAT Student", existing_roles["student"].id
    )
    await session.flush()
    print("  [ok] Demo users ready: admin@omnitest.com, student@omnitest.com")
    return admin_user.id


async def _seed_materials(session: AsyncSession, admin_id: int | None) -> None:
    """Insert missing starter study guides and embed their chunks when Gemini is reachable."""
    material_service = MaterialService(MaterialRepository(session))
    inserted = 0
    for item in MATERIALS_DATA:
        existing = (
            (await session.execute(select(StudyMaterial).where(StudyMaterial.title == item["title"]))).scalars().first()
        )
        if existing:
            continue
        mat = StudyMaterial(**item, created_by=admin_id)
        session.add(mat)
        await session.flush()
        inserted += 1
        try:
            await material_service.ingest_material_chunks(mat.id, mat.content)
        except Exception as exc:
            print(f"  [warn] Skipping embedding for seeded material '{mat.title}': {exc}")
    print(f"  [ok] Seeded {inserted} new study material(s) ({len(MATERIALS_DATA)} total checked)")


async def _seed_quizzes(session: AsyncSession, admin_id: int | None) -> None:
    """Insert missing starter practice quizzes."""
    candidates = build_seed_quizzes(admin_id)
    inserted = 0
    for quiz in candidates:
        existing = (await session.execute(select(Quiz).where(Quiz.title == quiz.title))).scalars().first()
        if not existing:
            session.add(quiz)
            inserted += 1
    await session.flush()
    print(f"  [ok] Seeded {inserted} new quiz(zes) ({len(candidates)} total checked)")


async def _seed_essay_prompts(session: AsyncSession, admin_id: int | None) -> None:
    """Insert missing starter essay prompts and commit the seeding transaction."""
    candidates = build_seed_prompts(admin_id)
    inserted = 0
    for prompt in candidates:
        existing = (
            (await session.execute(select(EssayPrompt).where(EssayPrompt.prompt_text == prompt.prompt_text)))
            .scalars()
            .first()
        )
        if not existing:
            session.add(prompt)
            inserted += 1
    await session.commit()
    print(f"  [ok] Seeded {inserted} new essay prompt(s) ({len(candidates)} total checked)")


async def seed() -> None:
    """Run all idempotent database seed steps inside one async session."""
    print("Starting OmniTest database seeding...")
    async with AsyncSessionLocal() as session:
        admin_id = await _seed_roles_and_users(session)
        await _seed_materials(session, admin_id)
        await _seed_quizzes(session, admin_id)
        await _seed_essay_prompts(session, admin_id)
    print("OmniTest database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
