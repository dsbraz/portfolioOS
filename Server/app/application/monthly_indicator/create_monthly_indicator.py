from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.period import Period
from app.domain.models.startup import Startup
from app.domain.repositories import MonthlyIndicatorRepository
from app.domain.validators import validate_period_not_future


# Fields an upsert overwrites when the incoming value is present; absence never
# erases what is stored.
_MERGED_FIELDS = (
    "total_revenue",
    "recurring_revenue_pct",
    "gross_margin_pct",
    "cash_balance",
    "headcount",
    "ebitda_burn",
    "achievements",
    "challenges",
    "comments",
)


class CreateMonthlyIndicator:
    def __init__(self, repository: MonthlyIndicatorRepository) -> None:
        self._repository = repository

    async def execute(
        self, startup: Startup, indicator: MonthlyIndicator, *, through_link: bool
    ) -> MonthlyIndicator:
        """Store or merge a period's indicator.

        `through_link` says whether the investee sent it by a reporting link or
        the fund entered it by hand: an exited startup accepts only the latter,
        and only up to its exit month.
        """
        validate_period_not_future(indicator.month, indicator.year)
        startup.ensure_accepts_indicator(
            Period(year=indicator.year, month=indicator.month),
            through_link=through_link,
        )

        stored, created = await self._repository.get_or_create(indicator)
        if created:
            return stored
        return await self._merge(stored, indicator)

    async def _merge(
        self, existing: MonthlyIndicator, incoming: MonthlyIndicator
    ) -> MonthlyIndicator:
        for field in _MERGED_FIELDS:
            value = getattr(incoming, field)
            if value is not None:
                setattr(existing, field, value)
        return await self._repository.update(existing)
