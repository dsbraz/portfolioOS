import uuid
from datetime import date

from fastapi import HTTPException, status

from app.domain.models.monthly_indicator import MonthlyIndicator
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository


class MonthlyIndicatorService:
    def __init__(self, repository: MonthlyIndicatorRepository):
        self._repository = repository

    async def list_indicators(
        self, startup_id: uuid.UUID
    ) -> tuple[list[MonthlyIndicator], int]:
        return await self._repository.get_all_by_startup(startup_id)

    async def get_indicator(
        self, indicator_id: uuid.UUID
    ) -> MonthlyIndicator | None:
        return await self._repository.get_by_id(indicator_id)

    async def get_latest_indicator(
        self, startup_id: uuid.UUID
    ) -> MonthlyIndicator | None:
        return await self._repository.get_latest_by_startup(startup_id)

    def _validate_period_not_future(self, month: int, year: int) -> None:
        today = date.today()
        if year > today.year or (year == today.year and month > today.month):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Periodo {month}/{year} nao pode ser no futuro",
            )

    async def create_indicator(
        self, indicator: MonthlyIndicator
    ) -> MonthlyIndicator:
        self._validate_period_not_future(indicator.month, indicator.year)
        if await self._repository.exists_for_month(
            indicator.startup_id, indicator.month, indicator.year
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Indicador para {indicator.month}/{indicator.year} já existe para esta startup",
            )
        return await self._repository.create(indicator)

    async def update_indicator(
        self, indicator: MonthlyIndicator, updates: dict
    ) -> MonthlyIndicator:
        month = updates.get("month", indicator.month)
        year = updates.get("year", indicator.year)
        self._validate_period_not_future(month, year)
        for field, value in updates.items():
            setattr(indicator, field, value)
        return await self._repository.update(indicator)

    async def delete_indicator(self, indicator: MonthlyIndicator) -> None:
        await self._repository.delete(indicator)
