from app.domain.models.executive import Executive
from app.domain.repositories import ExecutiveRepository
from app.domain.validators import validate_monthly_report_recipient


class UpdateExecutive:
    def __init__(self, repository: ExecutiveRepository) -> None:
        self._repository = repository

    async def execute(self, executive: Executive, updates: dict) -> Executive:
        # Checked on the merged result, before touching the record.
        validate_monthly_report_recipient(
            updates.get("receives_monthly_report", executive.receives_monthly_report),
            updates.get("email", executive.email),
        )
        for field, value in updates.items():
            setattr(executive, field, value)
        return await self._repository.update(executive)
