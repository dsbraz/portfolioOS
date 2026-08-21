"""Bootstrap the end-to-end stack: one known operator plus the demo scenario.

A fresh database has no users, and `POST /api/users` requires a session — so the
first operator cannot be created through the API. This script closes that
chicken-and-egg for the e2e stack only, and refuses to run anywhere that is not
an explicitly local environment.

The password lives here in the open on purpose: it belongs to a throwaway
database that exists for the length of a test run. Never point this at a
database that holds real data.
"""

import asyncio
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.user.register_user import RegisterUser
from app.domain.models.user import User
from app.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from app.repositories.user_repository import UserRepository
from scripts.seed_demo import ensure_development_environment, seed_demo

E2E_USERNAME = "e2e"
E2E_PASSWORD = "e2e-password-123"
E2E_EMAIL = "e2e@portfolioos.local"


async def ensure_e2e_user(session: AsyncSession) -> User:
    """Create the operator the suite logs in as, or return the existing one."""
    existing = await session.execute(select(User).where(User.username == E2E_USERNAME))
    user = existing.scalar_one_or_none()
    if user is not None:
        return user

    # Through the use case, so the password is hashed by the same rule the
    # application uses — a hand-rolled insert would drift from it silently.
    register = RegisterUser(UserRepository(session), BcryptPasswordHasher())
    return await register.execute(E2E_USERNAME, E2E_EMAIL, E2E_PASSWORD)


async def main() -> None:
    from app.database import async_session

    ensure_development_environment(os.environ.get("ENVIRONMENT", ""))
    async with async_session() as session, session.begin():
        user = await ensure_e2e_user(session)
        startup = await seed_demo(session)

    print(f'E2E ready: operator "{user.username}", scenario "{startup.name}"')


if __name__ == "__main__":
    asyncio.run(main())
