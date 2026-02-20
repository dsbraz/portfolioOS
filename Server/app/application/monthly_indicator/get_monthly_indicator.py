import uuid

from app.domain.models.monthly_indicator import MonthlyIndicator
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository


class GetMonthlyIndicator:
    def __init__(self, repository: MonthlyIndicatorRepository) -> None:
        self._repository = repository

    async def execute(self, indicator_id: uuid.UUID) -> MonthlyIndicator | None:
        return await self._repository.get_by_id(indicator_id)
