from datetime import date

from app.application.monthly_report.readmodels import (
    MonthlyReportPlan,
    MonthlyReportRecipient,
)
from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken
from app.domain.models.monthly_report_dispatch import DispatchKind
from app.domain.models.period import Period
from app.domain.models.startup import Startup
from app.domain.repositories import ExecutiveRepository, MonthlyIndicatorRepository


class PlanMonthlyReport:
    """Who gets the link of the month that just closed, and which link.

    `None` when there is nothing to send: the period is already reported (who is
    missing comes from the platform, never from the channel), or nobody marked
    has an address. Generating the link is a write, so it only happens when
    someone will receive it.
    """

    def __init__(
        self,
        executive_repository: ExecutiveRepository,
        indicator_repository: MonthlyIndicatorRepository,
    ) -> None:
        self._executive_repository = executive_repository
        self._indicator_repository = indicator_repository

    async def execute(
        self, startup: Startup, kind: DispatchKind
    ) -> MonthlyReportPlan | None:
        today = date.today()
        period = Period(year=today.year, month=today.month).previous()

        reported = await self._indicator_repository.get_by_startup_and_period(
            startup.id, period.month, period.year
        )
        if reported is not None:
            return None

        executives, _ = await self._executive_repository.get_all_by_startup(startup.id)
        recipients = tuple(
            MonthlyReportRecipient(e.id, e.name, e.email.strip())
            for e in executives
            if e.receives_monthly_report and e.email and e.email.strip()
        )
        if not recipients:
            return None

        # One link per (startup, period): the same one the panel shows.
        token, _ = await self._indicator_repository.get_or_create_token(
            MonthlyIndicatorToken(
                startup_id=startup.id, month=period.month, year=period.year
            )
        )
        return MonthlyReportPlan(
            startup_id=startup.id,
            startup_name=startup.name,
            period=period,
            kind=kind,
            form_token=token.token,
            recipients=recipients,
        )
