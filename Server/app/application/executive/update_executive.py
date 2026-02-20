from app.domain.models.executive import Executive
from app.repositories.executive_repository import ExecutiveRepository


class UpdateExecutive:
    def __init__(self, repository: ExecutiveRepository) -> None:
        self._repository = repository

    async def execute(self, executive: Executive, updates: dict) -> Executive:
        for field, value in updates.items():
            setattr(executive, field, value)
        return await self._repository.update(executive)
