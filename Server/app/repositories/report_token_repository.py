import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.report_token import ReportToken


class ReportTokenRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_token(self, token: uuid.UUID) -> ReportToken | None:
        result = await self._session.execute(
            select(ReportToken).where(ReportToken.token == token)
        )
        return result.scalar_one_or_none()

    async def get_by_startup_and_period(
        self, startup_id: uuid.UUID, month: int, year: int
    ) -> ReportToken | None:
        result = await self._session.execute(
            select(ReportToken).where(
                ReportToken.startup_id == startup_id,
                ReportToken.month == month,
                ReportToken.year == year,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_startup(
        self, startup_id: uuid.UUID
    ) -> tuple[list[ReportToken], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(ReportToken)
            .where(ReportToken.startup_id == startup_id)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(ReportToken)
            .where(ReportToken.startup_id == startup_id)
            .order_by(ReportToken.year.desc(), ReportToken.month.desc())
        )
        return list(result.scalars().all()), total

    async def create(self, report_token: ReportToken) -> ReportToken:
        self._session.add(report_token)
        await self._session.flush()
        await self._session.refresh(report_token)
        return report_token
