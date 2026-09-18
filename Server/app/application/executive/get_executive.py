import uuid

from app.domain.models.executive import Executive
from app.domain.repositories import ExecutiveRepository


class GetExecutive:
    def __init__(self, repository: ExecutiveRepository) -> None:
        self._repository = repository

    async def execute(self, executive_id: uuid.UUID) -> Executive | None:
        return await self._repository.get_by_id(executive_id)
