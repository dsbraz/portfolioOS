import uuid

from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken
from app.domain.validators import validate_period_not_future
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository


class CreateMonthlyIndicatorToken:
    def __init__(self, repository: MonthlyIndicatorRepository) -> None:
        self._repository = repository

    async def execute(
        self, startup_id: uuid.UUID, month: int, year: int
    ) -> MonthlyIndicatorToken:
        validate_period_not_future(month, year)

        existing = await self._repository.get_token_by_startup_and_period(
            startup_id, month, year
        )
        if existing:
            return existing

        token = MonthlyIndicatorToken(startup_id=startup_id, month=month, year=year)
        return await self._repository.create_token(token)
