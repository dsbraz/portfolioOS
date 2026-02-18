import uuid

from app.domain.models.deal import Deal, DealColumn
from app.repositories.deal_repository import DealRepository


class DealService:
    def __init__(self, repository: DealRepository):
        self._repository = repository

    async def list_deals(self) -> tuple[list[Deal], int]:
        return await self._repository.get_all()

    async def get_deal(self, deal_id: uuid.UUID) -> Deal | None:
        return await self._repository.get_by_id(deal_id)

    async def create_deal(self, deal: Deal) -> Deal:
        return await self._repository.create(deal)

    async def update_deal(self, deal: Deal, updates: dict) -> Deal:
        for field, value in updates.items():
            setattr(deal, field, value)
        return await self._repository.update(deal)

    async def move_deal(
        self, deal: Deal, column: DealColumn, position: int
    ) -> Deal:
        return await self._repository.move_deal(deal, column, position)

    async def delete_deal(self, deal: Deal) -> None:
        await self._repository.delete(deal)
