import uuid
from datetime import date

from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository


def _token_reference_period() -> tuple[int, int]:
    """Return (month, year) based on token rollover day (10th)."""
    today = date.today()
    months_back = 1 if today.day >= 10 else 2
    target_month = today.month - months_back
    target_year = today.year

    while target_month <= 0:
        target_month += 12
        target_year -= 1

    return target_month, target_year


class CreateMonthlyIndicatorToken:
    def __init__(
        self, repository: MonthlyIndicatorRepository
    ) -> None:
        self._repository = repository

    async def execute(
        self, startup_id: uuid.UUID
    ) -> MonthlyIndicatorToken:
        month, year = _token_reference_period()

        existing = await self._repository.get_token_by_startup_and_period(
            startup_id, month, year
        )
        if existing:
            return existing

        token = MonthlyIndicatorToken(
            startup_id=startup_id, month=month, year=year
        )
        return await self._repository.create_token(token)
