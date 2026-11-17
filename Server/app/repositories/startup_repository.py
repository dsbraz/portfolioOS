import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.startup import Startup


class StartupRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_all(
        self, tracked: bool | None = None
    ) -> tuple[list[Startup], int]:
        """All startups, or only those still tracked (`True`) or exited (`False`)."""
        query = select(Startup)
        if tracked is True:
            query = query.where(Startup.exited_on.is_(None))
        elif tracked is False:
            query = query.where(Startup.exited_on.is_not(None))

        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            query.order_by(Startup.created_at.desc())
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

    async def get_all_with_monthly_report_enabled(self) -> list[Startup]:
        result = await self._session.execute(
            select(Startup)
            .where(
                Startup.monthly_report_enabled.is_(True),
                # An exited startup has no reporting link; the plan re-checks
                # each one, since an exit can be recorded during the run.
                Startup.exited_on.is_(None),
            )
            .order_by(Startup.name.asc())
        )
        return list(result.scalars().all())
