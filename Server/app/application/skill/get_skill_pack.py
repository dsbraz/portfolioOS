import asyncio

from app.repositories.skill_repository import SkillRepository


class GetSkillPack:
    def __init__(self, repository: SkillRepository) -> None:
        self._repository = repository

    async def execute(self) -> bytes:
        return await asyncio.to_thread(self._repository.get_pack)
