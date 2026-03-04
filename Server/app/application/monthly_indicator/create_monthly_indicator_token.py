import uuid
from datetime import date

from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository


def _previous_month() -> tuple[int, int]:
    """Return (month, year) for the month before today."""
    today = date.today()
    if today.month == 1:
        return 12, today.year - 1
    return today.month - 1, today.year


class CreateMonthlyIndicatorToken:
    def __init__(
        self, repository: MonthlyIndicatorRepository
    ) -> None:
        self._repository = repository

    async def execute(
        self, startup_id: uuid.UUID
    ) -> MonthlyIndicatorToken:
        month, year = _previous_month()

        existing = await self._repository.get_token_by_startup_and_period(
            startup_id, month, year
        )
        if existing:
            return existing

        token = MonthlyIndicatorToken(
            startup_id=startup_id, month=month, year=year
        )
        return await self._repository.create_token(token)
