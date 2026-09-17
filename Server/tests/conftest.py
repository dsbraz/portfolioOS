import os
from collections.abc import AsyncGenerator
from urllib.parse import urlsplit, urlunsplit

# The suite runs against PostgreSQL — the database the application actually
# uses. SQLite could not exercise what this schema is made of: `UUID` comes
# from the postgresql dialect, the deal column is a native enum, and the
# get-or-create race recovery rests on a unique violation inside a savepoint.
#
# `DATABASE_URL` is required and points at the server, not at the database the
# tests use: a suite that shared the e2e database would read its seeded
# scenario as if it were its own fixtures. The tests get a database of their
# own, created here and dropped at the end.
_ADMIN_URL = os.environ.get("DATABASE_URL")
if not _ADMIN_URL:
    raise RuntimeError(
        "DATABASE_URL não definida — rode a suíte pelo compose:\n"
        "  docker compose -f docker-compose.e2e.yml run --rm server pytest"
    )

_TEST_DATABASE = "portfolio_test"


def _with_database(url: str, nome: str) -> str:
    partes = urlsplit(url)
    return urlunsplit(partes._replace(path=f"/{nome}"))


TEST_DATABASE_URL = _with_database(_ADMIN_URL, _TEST_DATABASE)

# Set BEFORE the application is imported: `app.database` builds its engine from
# this at import time, and nothing should point at the e2e database.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")

import asyncio  # noqa: E402

import pytest_asyncio  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings  # noqa: E402
from app.database import get_session  # noqa: E402
from app.domain.models.user import User  # noqa: E402
from app.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher  # noqa: E402
from app.infrastructure.jwt_token_generator import JwtTokenGenerator  # noqa: E402
from app.main import app  # noqa: E402

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def _recreate_database() -> None:
    """A database of its own, from scratch, on the server compose provides."""
    admin = create_async_engine(
        _with_database(_ADMIN_URL, "postgres"), isolation_level="AUTOCOMMIT"
    )
    async with admin.connect() as conn:
        # Anything still connected would block the drop — nothing should be,
        # but a crashed previous run leaves sessions behind.
        await conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :nome AND pid <> pg_backend_pid()"
            ),
            {"nome": _TEST_DATABASE},
        )
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{_TEST_DATABASE}"'))
        await conn.execute(text(f'CREATE DATABASE "{_TEST_DATABASE}"'))
    await admin.dispose()


def _migrate() -> None:
    """The schema comes from the migrations, not from the models.

    `metadata.create_all` would build what the models describe, which is
    precisely what a migration can drift away from. Running `upgrade head` here
    means a migration that disagrees with a model fails the suite instead of
    production.
    """
    config = Config(os.path.join(_RAIZ, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(_RAIZ, "alembic"))
    command.upgrade(config, "head")


# Once per session, at import: no event loop is running yet, and every test
# then starts from a schema that already exists.
asyncio.run(_recreate_database())
_migrate()

# NullPool: pytest-asyncio gives each test its own event loop, and a pooled
# asyncpg connection belongs to the loop that opened it. Reusing one across
# loops fails with "another operation is in progress" — a fresh connection per
# test costs nothing against a database in tmpfs.
engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
_hasher = BcryptPasswordHasher()
_token_gen = JwtTokenGenerator(
    settings.secret_key, settings.access_token_expire_minutes
)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """One test, one transaction, rolled back at the end.

    Isolation by transaction instead of by CREATE/DROP of the whole schema:
    the schema is built once per session, and a test never sees another's rows.
    `join_transaction_mode="create_savepoint"` is what makes the application's
    own `commit()` — the request cycle does one per call — release a savepoint
    rather than end the outer transaction, so the rollback below still undoes
    everything the test did.
    """
    async with engine.connect() as conexao:
        transacao = await conexao.begin()
        fabrica = async_sessionmaker(
            bind=conexao,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        async with fabrica() as session:
            yield session
        await transacao.rollback()


async def _create_test_user(session: AsyncSession) -> User:
    user = User(
        username="testadmin",
        email="testadmin@example.com",
        hashed_password=_hasher.hash("testpass123"),
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


def _override(session: AsyncSession):
    async def override_get_session():
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    return override_get_session


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    user = await _create_test_user(session)
    token = _token_gen.create_token(user)

    app.dependency_overrides[get_session] = _override(session)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def anon_client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_session] = _override(session)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def startup_id(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/startups",
        json={
            "name": "Test Startup",
            "sector": "tech",
            "investment_date": "2026-01-15",
        },
    )
    return resp.json()["id"]
