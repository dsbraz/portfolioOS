from app.domain.exceptions import ConflictError
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.validators import validate_period_not_future
from app.repositories.monthly_indicator_repository import (
    MonthlyIndicatorRepository,
)


class UpdateMonthlyIndicator:
    def __init__(self, repository: MonthlyIndicatorRepository) -> None:
        self._repository = repository

    async def execute(
        self, indicator: MonthlyIndicator, updates: dict
    ) -> MonthlyIndicator:
        month = updates.get("month", indicator.month)
        year = updates.get("year", indicator.year)
        validate_period_not_future(month, year)

        if (month, year) != (indicator.month, indicator.year):
            # Startup plus period is unique. Without this the write reaches the
            # constraint and surfaces as a 500 instead of a conflict the caller
            # can act on — and the edit dialog sends the period on every save.
            occupant = await self._repository.get_by_startup_and_period(
                indicator.startup_id, month, year
            )
            if occupant is not None and occupant.id != indicator.id:
                raise ConflictError(
                    f"Ja existe indicador para o periodo {month}/{year}"
                )

        for field, value in updates.items():
            setattr(indicator, field, value)
        return await self._repository.update(indicator)
