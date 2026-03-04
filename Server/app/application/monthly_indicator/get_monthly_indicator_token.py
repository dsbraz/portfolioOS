import uuid

from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository


class GetMonthlyIndicatorToken:
    def __init__(self, repository: MonthlyIndicatorRepository) -> None:
        self._repository = repository

    async def execute(self, token: uuid.UUID) -> MonthlyIndicatorToken | None:
        return await self._repository.get_token_by_value(token)
