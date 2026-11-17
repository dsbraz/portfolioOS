from datetime import date

from app.domain.exceptions import ConflictError, InvalidInputError
from app.domain.models.startup import ExitType, Startup
from app.domain.models.period import Period
from app.domain.repositories import MonthlyIndicatorRepository, StartupRepository
from app.domain.validators import validate_exit_not_before_investment


class RecordStartupExit:
    """Record that the fund left a startup, which stops tracking it.

    Nothing is deleted: indicators, meetings and executives stay readable.
    """

    def __init__(
        self,
        repository: StartupRepository,
        indicator_repository: MonthlyIndicatorRepository,
    ) -> None:
        self._repository = repository
        self._indicator_repository = indicator_repository

    async def execute(
        self,
        startup: Startup,
        exited_on: date,
        exit_type: ExitType,
        exit_notes: str | None,
    ) -> Startup:
        if startup.exited_on is not None:
            raise ConflictError("Saída da startup já registrada")
        if exited_on > date.today():
            raise InvalidInputError("Data da saída não pode ser no futuro")
        validate_exit_not_before_investment(startup.investment_date, exited_on)
        await self._ensure_no_report_after(startup, exited_on)

        startup.exited_on = exited_on
        startup.exit_type = exit_type
        startup.exit_notes = (exit_notes or "").strip() or None
        return await self._repository.update(startup)

    async def _ensure_no_report_after(self, startup: Startup, exited_on: date) -> None:
        """Months after the exit stop counting, so a report stored for one of
        them would silently drop out of the portfolio."""
        today = date.today()
        last = (
            await self._indicator_repository.get_last_reported_period_by_startups(
                [startup.id], today.month, today.year
            )
        ).get(startup.id)
        if last and last > Period(year=exited_on.year, month=exited_on.month):
            raise InvalidInputError(
                "Data da saída não pode ser anterior ao último mês reportado "
                f"({last.month:02d}/{last.year})"
            )
