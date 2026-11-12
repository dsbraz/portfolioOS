import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.monthly_report_dispatch import (
    DispatchKind,
    MonthlyReportDispatch,
)
from app.repositories.get_or_insert import get_or_insert


class MonthlyReportDispatchRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_or_create(
        self, dispatch: MonthlyReportDispatch
    ) -> tuple[MonthlyReportDispatch, bool]:
        """The stored send for this recipient, period and kind, or `dispatch` inserted."""
        return await get_or_insert(
            self._session,
            dispatch,
            lambda: self.find(
                dispatch.startup_id,
                dispatch.executive_id,
                dispatch.month,
                dispatch.year,
                dispatch.kind,
            ),
            f"Ja existe envio {dispatch.kind.value} para {dispatch.month}/{dispatch.year}",
        )

    async def update(self, dispatch: MonthlyReportDispatch) -> MonthlyReportDispatch:
        await self._session.flush()
        await self._session.refresh(dispatch)
        return dispatch

    async def get_all_by_startup(
        self, startup_id: uuid.UUID
    ) -> tuple[list[MonthlyReportDispatch], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(MonthlyReportDispatch)
            .where(MonthlyReportDispatch.startup_id == startup_id)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(MonthlyReportDispatch)
            .where(MonthlyReportDispatch.startup_id == startup_id)
            .order_by(
                MonthlyReportDispatch.year.desc(),
                MonthlyReportDispatch.month.desc(),
                MonthlyReportDispatch.sent_at.desc(),
            )
        )
        return list(result.scalars().all()), total

    async def find(
        self,
        startup_id: uuid.UUID,
        executive_id: uuid.UUID | None,
        month: int,
        year: int,
        kind: DispatchKind,
    ) -> MonthlyReportDispatch | None:
        result = await self._session.execute(
            select(MonthlyReportDispatch).where(
                MonthlyReportDispatch.startup_id == startup_id,
                MonthlyReportDispatch.executive_id == executive_id,
                MonthlyReportDispatch.month == month,
                MonthlyReportDispatch.year == year,
                MonthlyReportDispatch.kind == kind,
            )
        )
        return result.scalar_one_or_none()
