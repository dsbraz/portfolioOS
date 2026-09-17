import calendar
import uuid
from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from typing import Literal

from app.application.portfolio.readmodels import (
    HealthDistribution,
    PortfolioSummary,
    StartupSummary,
)
from app.domain.exceptions import InvalidInputError
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.period import Period
from app.domain.models.startup import Startup, StartupStatus
from app.domain.validators import validate_period_not_future
from app.repositories.board_meeting_repository import BoardMeetingRepository
from app.repositories.monthly_indicator_repository import (
    MonthlyIndicatorRepository,
)
from app.repositories.startup_repository import StartupRepository

MEETING_CUTOFF_DAYS = 90

RevenueDirection = Literal["up", "down", "neutral"]


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
        selected = self._resolve_period(month, year)

        startups, total = await self._startup_repo.get_all()
        if total == 0:
            return _empty_summary()

        startup_ids = [s.id for s in startups]
        previous = selected.previous()
        indicators = await self._indicator_repo.get_by_startups_and_period(
            startup_ids, selected.month, selected.year
        )
        previous_indicators = await self._indicator_repo.get_by_startups_and_period(
            startup_ids, previous.month, previous.year
        )
        accumulated_revenue = (
            await self._indicator_repo.get_accumulated_revenue_by_startups(
                startup_ids, selected.month, selected.year
            )
        )
        last_reported = await self._indicator_repo.get_last_reported_period_by_startups(
            startup_ids, selected.month, selected.year
        )
        ids_with_meetings = (
            await self._meeting_repo.get_startup_ids_with_recent_meetings(
                startup_ids,
                MEETING_CUTOFF_DAYS,
                _routines_reference_date(selected),
            )
        )

        revenue = _sum_revenue(indicators.values())
        variation_pct, variation_direction = self._calculate_revenue_variation(
            revenue, _sum_revenue(previous_indicators.values())
        )
        startups_with_report = sum(1 for sid in startup_ids if indicators.get(sid))

        return PortfolioSummary(
            total_startups=total,
            revenue=revenue,
            revenue_variation_pct=variation_pct,
            revenue_variation_direction=variation_direction,
            health=_health_distribution(startups),
            monthly_report_pct=_percentage(startups_with_report, total),
            routines_up_to_date_pct=_percentage(len(ids_with_meetings), total),
            startups=_build_rows(
                startups, indicators, accumulated_revenue, last_reported
            ),
        )

    def _resolve_period(self, month: int | None, year: int | None) -> Period:
        if month is None and year is None:
            today = date.today()
            return Period(year=today.year, month=today.month)

        if month is None or year is None:
            raise InvalidInputError("Mes e ano devem ser informados juntos")

        if month < 1 or month > 12:
            raise InvalidInputError("Mes deve estar entre 1 e 12")

        validate_period_not_future(month, year)
        return Period(year=year, month=month)

    def _calculate_revenue_variation(
        self, current_revenue: Decimal, previous_revenue: Decimal
    ) -> tuple[float | None, RevenueDirection]:
        if previous_revenue <= 0:
            return None, "neutral"

        variation = ((current_revenue - previous_revenue) / previous_revenue) * 100
        rounded_variation = round(float(variation), 1)
        if rounded_variation > 0:
            return rounded_variation, "up"
        if rounded_variation < 0:
            return rounded_variation, "down"
        return rounded_variation, "neutral"


def _empty_summary() -> PortfolioSummary:
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


def _health_distribution(startups: Iterable[Startup]) -> HealthDistribution:
    statuses = [s.status for s in startups]
    return HealthDistribution(
        healthy=statuses.count(StartupStatus.HEALTHY),
        warning=statuses.count(StartupStatus.WARNING),
        critical=statuses.count(StartupStatus.CRITICAL),
    )


def _sum_revenue(indicators: Iterable[MonthlyIndicator]) -> Decimal:
    return sum(
        (ind.total_revenue for ind in indicators if ind.total_revenue),
        Decimal("0"),
    )


def _percentage(part: int, total: int) -> float:
    return round((part / total) * 100, 1)


def _routines_reference_date(selected: Period) -> date:
    """Today for the current month; otherwise the last day of the selected month."""
    today = date.today()
    if selected == Period(year=today.year, month=today.month):
        return today
    last_day = calendar.monthrange(selected.year, selected.month)[1]
    return date(selected.year, selected.month, last_day)


def _build_rows(
    startups: Iterable[Startup],
    indicators: dict[uuid.UUID, MonthlyIndicator],
    accumulated_revenue: dict[uuid.UUID, Decimal],
    last_reported: dict[uuid.UUID, Period],
) -> list[StartupSummary]:
    return [
        _build_row(
            s,
            indicators.get(s.id),
            accumulated_revenue.get(s.id),
            last_reported.get(s.id),
        )
        for s in startups
    ]


def _build_row(
    startup: Startup,
    indicator: MonthlyIndicator | None,
    accumulated_revenue_ytd: Decimal | None,
    last_reported: Period | None,
) -> StartupSummary:
    return StartupSummary(
        startup=startup,
        total_revenue=indicator.total_revenue if indicator else None,
        cash_balance=indicator.cash_balance if indicator else None,
        ebitda_burn=indicator.ebitda_burn if indicator else None,
        headcount=indicator.headcount if indicator else None,
        accumulated_revenue_ytd=accumulated_revenue_ytd,
        last_reported_year=last_reported.year if last_reported else None,
        last_reported_month=last_reported.month if last_reported else None,
    )
