from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.validators import validate_period_not_future
from app.repositories.monthly_indicator_repository import (
    MonthlyIndicatorRepository,
)


class CreateMonthlyIndicator:
    def __init__(
        self, repository: MonthlyIndicatorRepository
    ) -> None:
        self._repository = repository

    async def execute(
        self, indicator: MonthlyIndicator
    ) -> MonthlyIndicator:
        validate_period_not_future(indicator.month, indicator.year)

        existing = await self._repository.get_by_startup_and_period(
            indicator.startup_id, indicator.month, indicator.year
        )
        if existing:
            fields = {
                "total_revenue", "recurring_revenue_pct", "gross_margin_pct",
                "cash_balance", "headcount", "ebitda_burn",
                "achievements", "challenges", "comments",
            }
            for field in fields:
                value = getattr(indicator, field)
                if value is not None:
                    setattr(existing, field, value)
            return await self._repository.update(existing)

        return await self._repository.create(indicator)
