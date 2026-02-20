import uuid

from app.domain.models.deal import Deal
from app.repositories.deal_repository import DealRepository


class GetDeal:
    def __init__(self, repository: DealRepository) -> None:
        self._repository = repository

    async def execute(self, deal_id: uuid.UUID) -> Deal | None:
        return await self._repository.get_by_id(deal_id)
