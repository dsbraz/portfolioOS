import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.executive import Executive


class ExecutiveRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_all_by_startup(
        self, startup_id: uuid.UUID
    ) -> tuple[list[Executive], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(Executive)
            .where(Executive.startup_id == startup_id)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(Executive)
            .where(Executive.startup_id == startup_id)
            .order_by(Executive.name.asc())
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, executive_id: uuid.UUID) -> Executive | None:
        result = await self._session.execute(
            select(Executive).where(Executive.id == executive_id)
        )
        return result.scalar_one_or_none()

    async def create(self, executive: Executive) -> Executive:
        self._session.add(executive)
        await self._session.flush()
        await self._session.refresh(executive)
        return executive

    async def update(self, executive: Executive) -> Executive:
        await self._session.flush()
        await self._session.refresh(executive)
        return executive

    async def delete(self, executive: Executive) -> None:
        await self._session.delete(executive)
        await self._session.flush()
