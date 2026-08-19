from app.domain.models.executive import Executive
from app.domain.validators import (
    normalize_contact_email,
    normalize_international_phone,
)
from app.repositories.executive_repository import ExecutiveRepository


class UpdateExecutive:
    def __init__(self, repository: ExecutiveRepository) -> None:
        self._repository = repository

    async def execute(self, executive: Executive, updates: dict) -> Executive:
        if "phone" in updates:
            updates = {
                **updates,
                "phone": normalize_international_phone(updates["phone"]),
            }
        if "email" in updates:
            updates = {**updates, "email": normalize_contact_email(updates["email"])}
        for field, value in updates.items():
            setattr(executive, field, value)
        return await self._repository.update(executive)
