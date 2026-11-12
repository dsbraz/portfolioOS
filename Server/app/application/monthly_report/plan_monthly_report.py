from datetime import date

from app.application.monthly_report.readmodels import (
    MonthlyReportPlan,
    MonthlyReportRecipient,
    MonthlyReportSkip,
)
from app.domain.models.executive import Executive
from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken
from app.domain.models.monthly_report_dispatch import DispatchKind
from app.domain.models.period import Period
from app.domain.models.startup import Startup
from app.domain.repositories import ExecutiveRepository, MonthlyIndicatorRepository
from app.domain.validators import validate_period_closed


class PlanMonthlyReport:
    """Who gets the link of the month that just closed, and which link.

    A `MonthlyReportSkip` when there is nothing to send: the period is already
    reported (who is missing comes from the platform, never from the channel),
    or nobody marked has an address. Generating the link is a write, so it only
    happens when someone will receive it.

    The period defaults to the month before today; a manual rerun after the
    month turned passes the one it means, so it retries that month instead of
    starting the next.
    """

    def __init__(
        self,
        executive_repository: ExecutiveRepository,
        indicator_repository: MonthlyIndicatorRepository,
    ) -> None:
        self._executive_repository = executive_repository
        self._indicator_repository = indicator_repository

    async def execute(
        self, startup: Startup, kind: DispatchKind, period: Period | None = None
    ) -> MonthlyReportPlan | MonthlyReportSkip:
        if period is None:
            today = date.today()
            period = Period(year=today.year, month=today.month).previous()
        validate_period_closed(period)

        reported = await self._indicator_repository.get_by_startup_and_period(
            startup.id, period.month, period.year
        )
        if reported is not None:
            return MonthlyReportSkip.ALREADY_REPORTED

        executives, _ = await self._executive_repository.get_all_by_startup(startup.id)
        recipients = _recipients(executives)
        if not recipients:
            return MonthlyReportSkip.NO_RECIPIENTS

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


def _recipients(executives: list[Executive]) -> tuple[MonthlyReportRecipient, ...]:
    """The marked executives with an address, one per inbox.

    The address is normalised once here, so the send record keyed by it treats
    `Ana@X.com ` and `ana@x.com` as the same inbox. When two executives share
    one, the first listed is the one greeted.
    """
    by_address: dict[str, MonthlyReportRecipient] = {}
    for executive in executives:
        address = (executive.email or "").strip().lower()
        if executive.receives_monthly_report and address:
            by_address.setdefault(
                address,
                MonthlyReportRecipient(executive.id, executive.name, address),
            )
    return tuple(by_address.values())
