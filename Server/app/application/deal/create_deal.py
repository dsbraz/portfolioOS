from app.domain.models.deal import Deal
from app.domain.repositories import DealRepository


class CreateDeal:
    def __init__(self, repository: DealRepository) -> None:
        self._repository = repository

    async def execute(self, deal: Deal) -> Deal:
        return await self._repository.create(deal)
