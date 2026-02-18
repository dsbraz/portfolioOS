import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.startup import Startup


class StartupRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_all(self) -> tuple[list[Startup], int]:
        count_result = await self._session.execute(
            select(func.count()).select_from(Startup)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(Startup).order_by(Startup.created_at.desc())
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, startup_id: uuid.UUID) -> Startup | None:
        result = await self._session.execute(
            select(Startup).where(Startup.id == startup_id)
        )
        return result.scalar_one_or_none()

    async def create(self, startup: Startup) -> Startup:
        self._session.add(startup)
        await self._session.flush()
        await self._session.refresh(startup)
        return startup

    async def update(self, startup: Startup) -> Startup:
        await self._session.flush()
        await self._session.refresh(startup)
        return startup

    async def delete(self, startup: Startup) -> None:
        await self._session.delete(startup)
        await self._session.flush()
