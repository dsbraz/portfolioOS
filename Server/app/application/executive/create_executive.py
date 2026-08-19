from app.domain.models.executive import Executive
from app.domain.validators import normalize_international_phone
from app.repositories.executive_repository import ExecutiveRepository


class CreateExecutive:
    def __init__(self, repository: ExecutiveRepository) -> None:
        self._repository = repository

    async def execute(self, executive: Executive) -> Executive:
        # Stored in E.164 so every consumer reads one shape; a number without
        # the country prefix is refused rather than guessed.
        executive.phone = normalize_international_phone(executive.phone)
        return await self._repository.create(executive)
