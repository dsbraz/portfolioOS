import uuid
from datetime import datetime

from sqlalchemy import select, update
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
        """The stored send for this address, period and kind, or `dispatch` inserted."""
        return await get_or_insert(
            self._session,
            dispatch,
            lambda: self.find(
                dispatch.startup_id,
                dispatch.recipient_email,
                dispatch.month,
                dispatch.year,
                dispatch.kind,
            ),
            f"Ja existe envio {dispatch.kind.value} para {dispatch.month}/{dispatch.year}",
        )

    async def get_by_id(self, dispatch_id: uuid.UUID) -> MonthlyReportDispatch | None:
        result = await self._session.execute(
            select(MonthlyReportDispatch).where(MonthlyReportDispatch.id == dispatch_id)
        )
        return result.scalar_one_or_none()

    async def reclaim_failed(
        self,
        dispatch: MonthlyReportDispatch,
        executive_id: uuid.UUID | None,
        attempted_at: datetime,
    ) -> MonthlyReportDispatch | None:
        """Claim a failed send for a retry, only if it is still failed.

        A conditional UPDATE, not read-then-write: when two runs overlap, the
        second waits on the row lock, re-reads it as no longer failed and
        updates nothing — so only one of them sends.
        """
        result = await self._session.execute(
            update(MonthlyReportDispatch)
            .where(
                MonthlyReportDispatch.id == dispatch.id,
                MonthlyReportDispatch.error.is_not(None),
            )
            .values(error=None, executive_id=executive_id, attempted_at=attempted_at)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount == 0:
            return None
        await self._session.refresh(dispatch)
        return dispatch

    async def update(self, dispatch: MonthlyReportDispatch) -> MonthlyReportDispatch:
        await self._session.flush()
        await self._session.refresh(dispatch)
        return dispatch

    async def get_all_by_startup(
        self, startup_id: uuid.UUID
    ) -> tuple[list[MonthlyReportDispatch], int]:
        # Unpaginated: the history of one startup is a few rows a month.
        result = await self._session.execute(
            select(MonthlyReportDispatch)
            .where(MonthlyReportDispatch.startup_id == startup_id)
            .order_by(
                MonthlyReportDispatch.year.desc(),
                MonthlyReportDispatch.month.desc(),
                MonthlyReportDispatch.attempted_at.desc(),
            )
        )
        items = list(result.scalars().all())
        return items, len(items)

    async def find(
        self,
        startup_id: uuid.UUID,
        recipient_email: str,
        month: int,
        year: int,
        kind: DispatchKind,
    ) -> MonthlyReportDispatch | None:
        result = await self._session.execute(
            select(MonthlyReportDispatch).where(
                MonthlyReportDispatch.startup_id == startup_id,
                MonthlyReportDispatch.recipient_email == recipient_email,
                MonthlyReportDispatch.month == month,
                MonthlyReportDispatch.year == year,
                MonthlyReportDispatch.kind == kind,
            )
        )
        return result.scalar_one_or_none()
