from datetime import date
from decimal import Decimal

from app.application.portfolio.readmodels import (
    HealthDistribution,
    PortfolioSummary,
    StartupSummary,
)
from app.domain.models.startup import StartupStatus
from app.repositories.board_meeting_repository import BoardMeetingRepository
from app.repositories.monthly_indicator_repository import (
    MonthlyIndicatorRepository,
)
from app.repositories.startup_repository import StartupRepository

MEETING_CUTOFF_DAYS = 90


class GetPortfolioSummary:
    def __init__(
        self,
        startup_repo: StartupRepository,
        indicator_repo: MonthlyIndicatorRepository,
        meeting_repo: BoardMeetingRepository,
    ) -> None:
        self._startup_repo = startup_repo
        self._indicator_repo = indicator_repo
        self._meeting_repo = meeting_repo

    async def execute(self) -> PortfolioSummary:
        startups, total = await self._startup_repo.get_all()

        if total == 0:
            return PortfolioSummary(
                total_startups=0,
                revenue=Decimal("0"),
                health=HealthDistribution(),
                monthly_report_pct=0.0,
                routines_up_to_date_pct=0.0,
                startups=[],
            )

        startup_ids = [s.id for s in startups]
        latest_indicators = (
            await self._indicator_repo.get_latest_by_startups(startup_ids)
        )

        healthy = warning = critical = 0
        for s in startups:
            if s.status == StartupStatus.HEALTHY:
                healthy += 1
            elif s.status == StartupStatus.WARNING:
                warning += 1
            elif s.status == StartupStatus.CRITICAL:
                critical += 1

        total_revenue = Decimal("0")
        for ind in latest_indicators.values():
            if ind.total_revenue:
                total_revenue += ind.total_revenue

        today = date.today()
        startups_with_report = sum(
            1
            for sid in startup_ids
            if (ind := latest_indicators.get(sid))
            and ind.month == today.month
            and ind.year == today.year
        )
        report_pct = (startups_with_report / total) * 100

        ids_with_meetings = (
            await self._meeting_repo.get_startup_ids_with_recent_meetings(
                startup_ids, MEETING_CUTOFF_DAYS
            )
        )
        routines_pct = (len(ids_with_meetings) / total) * 100

        monitoring_items = []
        for s in startups:
            ind = latest_indicators.get(s.id)
            monitoring_items.append(
                StartupSummary(
                    startup=s,
                    total_revenue=ind.total_revenue if ind else None,
                    cash_balance=ind.cash_balance if ind else None,
                    ebitda_burn=ind.ebitda_burn if ind else None,
                    headcount=ind.headcount if ind else None,
                )
            )

        return PortfolioSummary(
            total_startups=total,
            revenue=total_revenue,
            health=HealthDistribution(
                healthy=healthy, warning=warning, critical=critical
            ),
            monthly_report_pct=round(report_pct, 1),
            routines_up_to_date_pct=round(routines_pct, 1),
            startups=monitoring_items,
        )
