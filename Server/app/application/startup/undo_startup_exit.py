from app.domain.exceptions import ConflictError
from app.domain.models.startup import Startup
from app.domain.repositories import StartupRepository


class UndoStartupExit:
    """Clear a recorded exit, so a wrong entry never gets stuck."""

    def __init__(self, repository: StartupRepository) -> None:
        self._repository = repository

    async def execute(self, startup: Startup) -> Startup:
        if startup.exited_on is None:
            raise ConflictError("Startup nao tem saida registrada")

        startup.exited_on = None
        startup.exit_type = None
        startup.exit_notes = None
        return await self._repository.update(startup)
