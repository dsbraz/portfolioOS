import uuid
from datetime import date, timedelta

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.board_meeting import BoardMeeting
from app.domain.models.monthly_indicator import MonthlyIndicator


class PortfolioMonitoringRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_indicators(
        self, startup_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, MonthlyIndicator]:
        if not startup_ids:
            return {}

        latest_subq = (
            select(
                MonthlyIndicator.startup_id,
                func.max(
                    cast(MonthlyIndicator.year, Integer) * 100
                    + cast(MonthlyIndicator.month, Integer)
                ).label("max_period"),
            )
            .where(MonthlyIndicator.startup_id.in_(startup_ids))
            .group_by(MonthlyIndicator.startup_id)
            .subquery()
        )

        result = await self._session.execute(
            select(MonthlyIndicator).join(
                latest_subq,
                (MonthlyIndicator.startup_id == latest_subq.c.startup_id)
                & (
                    cast(MonthlyIndicator.year, Integer) * 100
                    + cast(MonthlyIndicator.month, Integer)
                    == latest_subq.c.max_period
                ),
            )
        )
        indicators = list(result.scalars().all())

        return {ind.startup_id: ind for ind in indicators}

    async def get_startup_ids_with_recent_meetings(
        self, startup_ids: list[uuid.UUID], cutoff_days: int
    ) -> set[uuid.UUID]:
        if not startup_ids:
            return set()

        cutoff = date.today() - timedelta(days=cutoff_days)
        result = await self._session.execute(
            select(BoardMeeting.startup_id)
            .where(
                BoardMeeting.startup_id.in_(startup_ids),
                BoardMeeting.meeting_date >= cutoff,
            )
            .distinct()
        )
        return set(result.scalars().all())
