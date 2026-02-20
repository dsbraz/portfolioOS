from app.domain.models.deal import Deal, DealColumn
from app.repositories.deal_repository import DealRepository


class MoveDeal:
    def __init__(self, repository: DealRepository) -> None:
        self._repository = repository

    async def execute(
        self, deal: Deal, column: DealColumn, position: int
    ) -> Deal:
        return await self._repository.move_deal(deal, column, position)
