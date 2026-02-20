from app.domain.models.deal import Deal
from app.repositories.deal_repository import DealRepository


class UpdateDeal:
    def __init__(self, repository: DealRepository) -> None:
        self._repository = repository

    async def execute(self, deal: Deal, updates: dict) -> Deal:
        for field, value in updates.items():
            setattr(deal, field, value)
        return await self._repository.update(deal)
