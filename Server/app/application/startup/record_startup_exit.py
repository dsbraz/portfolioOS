from datetime import date

from app.domain.exceptions import ConflictError, InvalidInputError
from app.domain.models.startup import ExitType, Startup
from app.domain.repositories import StartupRepository


class RecordStartupExit:
    """Record that the fund left a startup, which stops tracking it.

    Nothing is deleted: indicators, meetings and executives stay readable.
    """

    def __init__(self, repository: StartupRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        startup: Startup,
        exited_on: date,
        exit_type: ExitType,
        exit_notes: str | None,
    ) -> Startup:
        if startup.exited_on is not None:
            raise ConflictError("Saida da startup ja registrada")
        if exited_on > date.today():
            raise InvalidInputError("Data da saida nao pode ser no futuro")
        if exited_on < startup.investment_date:
            raise InvalidInputError(
                "Data da saida nao pode ser anterior ao investimento"
            )

        startup.exited_on = exited_on
        startup.exit_type = exit_type
        startup.exit_notes = (exit_notes or "").strip() or None
        return await self._repository.update(startup)
