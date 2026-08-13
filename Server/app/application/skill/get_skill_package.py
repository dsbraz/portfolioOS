from app.repositories.skill_repository import SkillRepository


class GetSkillPackage:
    def __init__(self, repository: SkillRepository) -> None:
        self._repository = repository

    async def execute(self, name: str) -> bytes | None:
        return self._repository.get_package(name)
