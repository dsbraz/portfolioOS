from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.validators import validate_period_not_future
from app.repositories.monthly_indicator_repository import (
    MonthlyIndicatorRepository,
)


class UpdateMonthlyIndicator:
    def __init__(
        self, repository: MonthlyIndicatorRepository
    ) -> None:
        self._repository = repository

    async def execute(
        self, indicator: MonthlyIndicator, updates: dict
    ) -> MonthlyIndicator:
        month = updates.get("month", indicator.month)
        year = updates.get("year", indicator.year)
        validate_period_not_future(month, year)

        for field, value in updates.items():
            setattr(indicator, field, value)
        return await self._repository.update(indicator)
