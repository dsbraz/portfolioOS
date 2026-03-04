import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken


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

    async def get_by_startup_and_period(
        self, startup_id: uuid.UUID, month: int, year: int
    ) -> MonthlyIndicator | None:
        result = await self._session.execute(
            select(MonthlyIndicator).where(
                MonthlyIndicator.startup_id == startup_id,
                MonthlyIndicator.month == month,
                MonthlyIndicator.year == year,
            )
        )
        return result.scalar_one_or_none()

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

    async def get_by_startups_and_period(
        self, startup_ids: list[uuid.UUID], month: int, year: int
    ) -> dict[uuid.UUID, MonthlyIndicator]:
        if not startup_ids:
            return {}

        result = await self._session.execute(
            select(MonthlyIndicator).where(
                MonthlyIndicator.startup_id.in_(startup_ids),
                MonthlyIndicator.month == month,
                MonthlyIndicator.year == year,
            )
        )
        indicators = list(result.scalars().all())

        return {ind.startup_id: ind for ind in indicators}

    # --- Token methods ---

    async def get_token_by_value(
        self, token: uuid.UUID
    ) -> MonthlyIndicatorToken | None:
        result = await self._session.execute(
            select(MonthlyIndicatorToken).where(
                MonthlyIndicatorToken.token == token
            )
        )
        return result.scalar_one_or_none()

    async def get_token_by_startup_and_period(
        self, startup_id: uuid.UUID, month: int, year: int
    ) -> MonthlyIndicatorToken | None:
        result = await self._session.execute(
            select(MonthlyIndicatorToken).where(
                MonthlyIndicatorToken.startup_id == startup_id,
                MonthlyIndicatorToken.month == month,
                MonthlyIndicatorToken.year == year,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_tokens_by_startup(
        self, startup_id: uuid.UUID
    ) -> tuple[list[MonthlyIndicatorToken], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(MonthlyIndicatorToken)
            .where(MonthlyIndicatorToken.startup_id == startup_id)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(MonthlyIndicatorToken)
            .where(MonthlyIndicatorToken.startup_id == startup_id)
            .order_by(
                MonthlyIndicatorToken.year.desc(),
                MonthlyIndicatorToken.month.desc(),
            )
        )
        return list(result.scalars().all()), total

    async def create_token(
        self, token: MonthlyIndicatorToken
    ) -> MonthlyIndicatorToken:
        self._session.add(token)
        await self._session.flush()
        await self._session.refresh(token)
        return token
