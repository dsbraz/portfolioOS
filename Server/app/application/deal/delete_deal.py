from app.domain.models.deal import Deal
from app.repositories.deal_repository import DealRepository


class DeleteDeal:
    def __init__(self, repository: DealRepository) -> None:
        self._repository = repository

    async def execute(self, deal: Deal) -> None:
        await self._repository.delete(deal)
