import uuid

from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.repositories import MonthlyIndicatorRepository


class ListMonthlyIndicators:
    def __init__(self, repository: MonthlyIndicatorRepository) -> None:
        self._repository = repository

    async def execute(
        self, startup_id: uuid.UUID
    ) -> tuple[list[MonthlyIndicator], int]:
        return await self._repository.get_all_by_startup(startup_id)
