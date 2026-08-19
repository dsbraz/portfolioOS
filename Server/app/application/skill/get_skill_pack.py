from app.repositories.skill_repository import SkillRepository


class GetSkillPack:
    def __init__(self, repository: SkillRepository) -> None:
        self._repository = repository

    async def execute(self) -> bytes:
        return self._repository.get_pack()
