from app.domain.exceptions import ConflictError
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

        if await self._repository.exists_for_month(
            indicator.startup_id, indicator.month, indicator.year
        ):
            raise ConflictError(
                f"Indicador para {indicator.month}/{indicator.year} "
                f"já existe para esta startup"
            )

        return await self._repository.create(indicator)
