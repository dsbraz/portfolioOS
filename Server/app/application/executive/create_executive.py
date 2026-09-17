from app.domain.models.executive import Executive
from app.repositories.executive_repository import ExecutiveRepository


class CreateExecutive:
    def __init__(self, repository: ExecutiveRepository) -> None:
        self._repository = repository

    async def execute(self, executive: Executive) -> Executive:
        return await self._repository.create(executive)
