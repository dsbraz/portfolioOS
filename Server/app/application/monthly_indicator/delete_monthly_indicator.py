from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.repositories import MonthlyIndicatorRepository


class DeleteMonthlyIndicator:
    def __init__(self, repository: MonthlyIndicatorRepository) -> None:
        self._repository = repository

    async def execute(self, indicator: MonthlyIndicator) -> None:
        await self._repository.delete(indicator)
