from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.config import settings


def _engine_options(database_url: str) -> dict:
    """Pool tuning only where the dialect has a pool to tune.

    SQLite runs on `StaticPool`/`NullPool`, which reject `pool_size` and
    `max_overflow` outright — passing them raises at import time, before a
    single query. That made the application impossible to import against
    SQLite, which is exactly what a test run or a throwaway local check wants
    to do.
    """
    if database_url.startswith("sqlite"):
        return {}
    return {
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_pre_ping": settings.db_pool_pre_ping,
    }


engine = create_async_engine(
    settings.database_url,
    **_engine_options(settings.database_url),
)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
