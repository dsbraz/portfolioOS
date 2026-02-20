from app.domain.models.deal import Deal
from app.repositories.deal_repository import DealRepository


class ListDeals:
    def __init__(self, repository: DealRepository) -> None:
        self._repository = repository

    async def execute(self) -> tuple[list[Deal], int]:
        return await self._repository.get_all()
