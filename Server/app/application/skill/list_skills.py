from app.domain.models.skill import Skill
from app.repositories.skill_repository import SkillRepository


class ListSkills:
    def __init__(self, repository: SkillRepository) -> None:
        self._repository = repository

    async def execute(self) -> tuple[list[Skill], int]:
        return self._repository.get_all()
