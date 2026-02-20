import uuid

from app.domain.models.executive import Executive
from app.repositories.executive_repository import ExecutiveRepository


class ListExecutives:
    def __init__(self, repository: ExecutiveRepository) -> None:
        self._repository = repository

    async def execute(self, startup_id: uuid.UUID) -> tuple[list[Executive], int]:
        return await self._repository.get_all_by_startup(startup_id)
