import calendar
from datetime import date
from decimal import Decimal

from app.application.portfolio.readmodels import (
    HealthDistribution,
    PortfolioSummary,
    StartupSummary,
)
from app.domain.models.startup import StartupStatus
from app.domain.validators import validate_period_not_future
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

    async def execute(
        self, month: int | None = None, year: int | None = None
    ) -> PortfolioSummary:
        selected_month, selected_year = self._resolve_period(month, year)

        startups, total = await self._startup_repo.get_all()

        if total == 0:
            return PortfolioSummary(
                total_startups=0,
                revenue=Decimal("0"),
                revenue_variation_pct=None,
                revenue_variation_direction="neutral",
                health=HealthDistribution(),
                monthly_report_pct=0.0,
                routines_up_to_date_pct=0.0,
                startups=[],
            )

        startup_ids = [s.id for s in startups]
        previous_month, previous_year = self._get_previous_period(
            selected_month, selected_year
        )
        indicators_by_period = (
            await self._indicator_repo.get_by_startups_and_period(
                startup_ids, selected_month, selected_year
            )
        )
        previous_indicators_by_period = (
            await self._indicator_repo.get_by_startups_and_period(
                startup_ids, previous_month, previous_year
            )
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
        for ind in indicators_by_period.values():
            if ind.total_revenue:
                total_revenue += ind.total_revenue

        previous_total_revenue = Decimal("0")
        for ind in previous_indicators_by_period.values():
            if ind.total_revenue:
                previous_total_revenue += ind.total_revenue

        revenue_variation_pct, revenue_variation_direction = (
            self._calculate_revenue_variation(
                total_revenue, previous_total_revenue
            )
        )

        startups_with_report = sum(
            1
            for sid in startup_ids
            if indicators_by_period.get(sid)
        )
        report_pct = (startups_with_report / total) * 100

        today = date.today()
        if selected_month == today.month and selected_year == today.year:
            routines_reference_date = today
        else:
            routines_reference_date = date(
                selected_year,
                selected_month,
                calendar.monthrange(selected_year, selected_month)[1],
            )

        ids_with_meetings = (
            await self._meeting_repo.get_startup_ids_with_recent_meetings(
                startup_ids,
                MEETING_CUTOFF_DAYS,
                routines_reference_date,
            )
        )
        routines_pct = (len(ids_with_meetings) / total) * 100

        monitoring_items = []
        for s in startups:
            ind = indicators_by_period.get(s.id)
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
            revenue_variation_pct=revenue_variation_pct,
            revenue_variation_direction=revenue_variation_direction,
            health=HealthDistribution(
                healthy=healthy, warning=warning, critical=critical
            ),
            monthly_report_pct=round(report_pct, 1),
            routines_up_to_date_pct=round(routines_pct, 1),
            startups=monitoring_items,
        )

    def _resolve_period(
        self, month: int | None, year: int | None
    ) -> tuple[int, int]:
        if month is None and year is None:
            today = date.today()
            return today.month, today.year

        if month is None or year is None:
            raise ValueError("Mes e ano devem ser informados juntos")

        if month < 1 or month > 12:
            raise ValueError("Mes deve estar entre 1 e 12")

        validate_period_not_future(month, year)
        return month, year

    def _get_previous_period(self, month: int, year: int) -> tuple[int, int]:
        if month == 1:
            return 12, year - 1
        return month - 1, year

    def _calculate_revenue_variation(
        self, current_revenue: Decimal, previous_revenue: Decimal
    ) -> tuple[float | None, str]:
        if previous_revenue <= 0:
            return None, "neutral"

        variation = ((current_revenue - previous_revenue) / previous_revenue) * 100
        rounded_variation = round(float(variation), 1)
        if rounded_variation > 0:
            return rounded_variation, "up"
        if rounded_variation < 0:
            return rounded_variation, "down"
        return rounded_variation, "neutral"
