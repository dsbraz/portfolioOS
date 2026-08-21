"""Engine options must match the dialect's pool.

Regression: the engine passed `pool_size`/`max_overflow` unconditionally, and
SQLite's StaticPool rejects them — so `import app.database` raised a TypeError
before any query. CI caught it; nothing local did, because the development
container always supplies a PostgreSQL URL.
"""

from app.database import _engine_options


def test_sqlite_gets_no_pool_tuning():
    assert _engine_options("sqlite+aiosqlite://") == {}
    assert _engine_options("sqlite+aiosqlite:///./qualquer.db") == {}


def test_postgres_keeps_its_pool_tuning():
    opcoes = _engine_options("postgresql+asyncpg://user:pass@host/db")

    assert set(opcoes) == {"pool_size", "max_overflow", "pool_pre_ping"}


def test_the_application_imports_against_sqlite():
    # The import itself is the assertion: it is what used to blow up.
    import app.main

    assert app.main.app is not None
