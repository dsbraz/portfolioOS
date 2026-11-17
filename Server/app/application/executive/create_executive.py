from app.domain.models.executive import Executive
from app.domain.repositories import ExecutiveRepository
from app.domain.validators import validate_monthly_report_recipient


class CreateExecutive:
    def __init__(self, repository: ExecutiveRepository) -> None:
        self._repository = repository

    async def execute(self, executive: Executive) -> Executive:
        validate_monthly_report_recipient(
            bool(executive.receives_monthly_report), executive.email
        )
        return await self._repository.create(executive)
