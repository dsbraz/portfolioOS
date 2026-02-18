import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.monthly_indicator import MonthlyIndicator


class MonthlyIndicatorRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_all_by_startup(
        self, startup_id: uuid.UUID
    ) -> tuple[list[MonthlyIndicator], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(MonthlyIndicator)
            .where(MonthlyIndicator.startup_id == startup_id)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(MonthlyIndicator)
            .where(MonthlyIndicator.startup_id == startup_id)
            .order_by(MonthlyIndicator.year.desc(), MonthlyIndicator.month.desc())
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, indicator_id: uuid.UUID) -> MonthlyIndicator | None:
        result = await self._session.execute(
            select(MonthlyIndicator).where(MonthlyIndicator.id == indicator_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_by_startup(
        self, startup_id: uuid.UUID
    ) -> MonthlyIndicator | None:
        result = await self._session.execute(
            select(MonthlyIndicator)
            .where(MonthlyIndicator.startup_id == startup_id)
            .order_by(MonthlyIndicator.year.desc(), MonthlyIndicator.month.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def exists_for_month(
        self, startup_id: uuid.UUID, month: int, year: int
    ) -> bool:
        result = await self._session.execute(
            select(func.count())
            .select_from(MonthlyIndicator)
            .where(
                MonthlyIndicator.startup_id == startup_id,
                MonthlyIndicator.month == month,
                MonthlyIndicator.year == year,
            )
        )
        return result.scalar_one() > 0

    async def create(self, indicator: MonthlyIndicator) -> MonthlyIndicator:
        self._session.add(indicator)
        await self._session.flush()
        await self._session.refresh(indicator)
        return indicator

    async def update(self, indicator: MonthlyIndicator) -> MonthlyIndicator:
        await self._session.flush()
        await self._session.refresh(indicator)
        return indicator

    async def delete(self, indicator: MonthlyIndicator) -> None:
        await self._session.delete(indicator)
        await self._session.flush()
