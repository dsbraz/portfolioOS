import uuid

from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken
from app.domain.repositories import MonthlyIndicatorRepository
from app.domain.validators import validate_period_not_future


class CreateMonthlyIndicatorToken:
    def __init__(self, repository: MonthlyIndicatorRepository) -> None:
        self._repository = repository

    async def execute(
        self, startup_id: uuid.UUID, month: int, year: int
    ) -> MonthlyIndicatorToken:
        validate_period_not_future(month, year)

        # One link per (startup, period): an existing one is returned as is.
        token, _ = await self._repository.get_or_create_token(
            MonthlyIndicatorToken(startup_id=startup_id, month=month, year=year)
        )
        return token
