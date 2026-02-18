from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.board_meeting import BoardMeeting
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.startup import Startup, StartupStatus


class PortfolioMonitoringService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_summary(self) -> dict:
        startups_result = await self._session.execute(
            select(Startup).order_by(Startup.name.asc())
        )
        startups = list(startups_result.scalars().all())
        total = len(startups)

        if total == 0:
            return {
                "total_startups": 0,
                "portfolio_revenue": Decimal("0"),
                "portfolio_health": {"healthy": 0, "warning": 0, "critical": 0},
                "monthly_report_pct": 0.0,
                "routines_up_to_date_pct": 0.0,
                "startups": [],
            }

        startup_ids = [s.id for s in startups]

        latest_indicators = await self._get_latest_indicators(startup_ids)

        health = {"healthy": 0, "warning": 0, "critical": 0}
        for s in startups:
            if s.status == StartupStatus.HEALTHY:
                health["healthy"] += 1
            elif s.status == StartupStatus.WARNING:
                health["warning"] += 1
            elif s.status == StartupStatus.CRITICAL:
                health["critical"] += 1

        portfolio_revenue = Decimal("0")
        for ind in latest_indicators.values():
            if ind.get("total_revenue"):
                portfolio_revenue += ind["total_revenue"]

        today = date.today()
        current_month = today.month
        current_year = today.year
        startups_with_report = 0
        for sid in startup_ids:
            ind = latest_indicators.get(sid)
            if ind and ind.get("month") == current_month and ind.get("year") == current_year:
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
            ind = latest_indicators.get(s.id, {})
            monitoring_items.append({
                "startup": s,
                "total_revenue": ind.get("total_revenue"),
                "cash_balance": ind.get("cash_balance"),
                "ebitda_burn": ind.get("ebitda_burn"),
                "headcount": ind.get("headcount"),
            })

        return {
            "total_startups": total,
            "portfolio_revenue": portfolio_revenue,
            "portfolio_health": health,
            "monthly_report_pct": round(report_pct, 1),
            "routines_up_to_date_pct": round(routines_pct, 1),
            "startups": monitoring_items,
        }

    async def _get_latest_indicators(
        self, startup_ids: list,
    ) -> dict:
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

        return {
            ind.startup_id: {
                "month": ind.month,
                "year": ind.year,
                "total_revenue": ind.total_revenue,
                "cash_balance": ind.cash_balance,
                "ebitda_burn": ind.ebitda_burn,
                "headcount": ind.headcount,
            }
            for ind in indicators
        }
