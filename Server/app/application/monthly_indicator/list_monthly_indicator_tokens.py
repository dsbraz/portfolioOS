import uuid

from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository


class ListMonthlyIndicatorTokens:
    def __init__(self, repository: MonthlyIndicatorRepository) -> None:
        self._repository = repository

    async def execute(
        self, startup_id: uuid.UUID
    ) -> tuple[list[MonthlyIndicatorToken], int]:
        return await self._repository.get_all_tokens_by_startup(startup_id)
