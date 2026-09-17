from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.validators import validate_period_not_future
from app.repositories.monthly_indicator_repository import (
    MonthlyIndicatorRepository,
)

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

    async def execute(self, indicator: MonthlyIndicator) -> MonthlyIndicator:
        validate_period_not_future(indicator.month, indicator.year)

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
