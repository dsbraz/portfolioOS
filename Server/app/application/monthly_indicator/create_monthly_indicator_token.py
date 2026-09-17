import uuid

from app.domain.exceptions import ConflictError
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
        try:
            return await self._repository.create_token(token)
        except ConflictError:
            # Lost the insert race. One link per (startup, period) is the
            # contract — including here, so a batch run returns the link that
            # exists instead of an error.
            winner = await self._repository.get_token_by_startup_and_period(
                startup_id, month, year
            )
            if winner is None:
                raise
            return winner
