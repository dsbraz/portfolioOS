import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.board_meeting import BoardMeeting
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.portfolio_summary import (
    HealthDistribution,
    PortfolioSummary,
    StartupMonitoringItem,
)
from app.domain.models.startup import Startup, StartupStatus


class PortfolioMonitoringService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_summary(self) -> PortfolioSummary:
        startups_result = await self._session.execute(
            select(Startup).order_by(Startup.name.asc())
        )
        startups = list(startups_result.scalars().all())
        total = len(startups)

        if total == 0:
            return PortfolioSummary(
                total_startups=0,
                portfolio_revenue=Decimal("0"),
                portfolio_health=HealthDistribution(),
                monthly_report_pct=0.0,
                routines_up_to_date_pct=0.0,
                startups=[],
            )

        startup_ids = [s.id for s in startups]

        latest_indicators = await self._get_latest_indicators(startup_ids)

        healthy = warning = critical = 0
        for s in startups:
            if s.status == StartupStatus.HEALTHY:
                healthy += 1
            elif s.status == StartupStatus.WARNING:
                warning += 1
            elif s.status == StartupStatus.CRITICAL:
                critical += 1

        portfolio_revenue = Decimal("0")
        for ind in latest_indicators.values():
            if ind.total_revenue:
                portfolio_revenue += ind.total_revenue

        today = date.today()
        current_month = today.month
        current_year = today.year
        startups_with_report = 0
        for sid in startup_ids:
            ind = latest_indicators.get(sid)
            if ind and ind.month == current_month and ind.year == current_year:
                startups_with_report += 1
        report_pct = (startups_with_report / total) * 100

        cutoff = today - timedelta(days=90)
        meetings_result = await self._session.execute(
            select(BoardMeeting.startup_id)
            .where(
                BoardMeeting.startup_id.in_(startup_ids),
                BoardMeeting.meeting_date >= cutoff,
            )
            .distinct()
        )
        startups_with_meeting = len(list(meetings_result.scalars().all()))
        routines_pct = (startups_with_meeting / total) * 100

        monitoring_items = []
        for s in startups:
            ind = latest_indicators.get(s.id)
            monitoring_items.append(
                StartupMonitoringItem(
                    startup=s,
                    total_revenue=ind.total_revenue if ind else None,
                    cash_balance=ind.cash_balance if ind else None,
                    ebitda_burn=ind.ebitda_burn if ind else None,
                    headcount=ind.headcount if ind else None,
                )
            )

        return PortfolioSummary(
            total_startups=total,
            portfolio_revenue=portfolio_revenue,
            portfolio_health=HealthDistribution(
                healthy=healthy, warning=warning, critical=critical,
            ),
            monthly_report_pct=round(report_pct, 1),
            routines_up_to_date_pct=round(routines_pct, 1),
            startups=monitoring_items,
        )

    async def _get_latest_indicators(
        self, startup_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, MonthlyIndicator]:
        latest_subq = (
            select(
                MonthlyIndicator.startup_id,
                func.max(
                    cast(MonthlyIndicator.year, Integer) * 100 + cast(MonthlyIndicator.month, Integer)
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
                    cast(MonthlyIndicator.year, Integer) * 100 + cast(MonthlyIndicator.month, Integer)
                    == latest_subq.c.max_period
                ),
            )
        )
        indicators = list(result.scalars().all())

        return {ind.startup_id: ind for ind in indicators}
