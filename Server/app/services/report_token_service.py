import uuid
from datetime import date

from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.report_token import ReportToken
from app.domain.models.startup import Startup
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository
from app.repositories.report_token_repository import ReportTokenRepository
from app.repositories.startup_repository import StartupRepository


class ReportTokenService:
    def __init__(
        self,
        token_repo: ReportTokenRepository,
        startup_repo: StartupRepository,
        indicator_repo: MonthlyIndicatorRepository,
    ):
        self._token_repo = token_repo
        self._startup_repo = startup_repo
        self._indicator_repo = indicator_repo

    def _validate_period_not_future(self, month: int, year: int) -> None:
        today = date.today()
        if year > today.year or (year == today.year and month > today.month):
            raise ValueError(
                f"Periodo {month}/{year} nao pode ser no futuro"
            )

    async def get_token_by_value(
        self, token: uuid.UUID
    ) -> ReportToken | None:
        return await self._token_repo.get_by_token(token)

    async def generate_token(
        self, startup_id: uuid.UUID, month: int, year: int
    ) -> ReportToken:
        self._validate_period_not_future(month, year)

        existing = await self._token_repo.get_by_startup_and_period(
            startup_id, month, year
        )
        if existing:
            return existing

        new_token = ReportToken(startup_id=startup_id, month=month, year=year)
        return await self._token_repo.create(new_token)

    async def list_tokens(
        self, startup_id: uuid.UUID
    ) -> tuple[list[ReportToken], int]:
        return await self._token_repo.get_all_by_startup(startup_id)

    async def get_form_context(
        self, report_token: ReportToken
    ) -> tuple[Startup | None, MonthlyIndicator | None]:
        startup = await self._startup_repo.get_by_id(report_token.startup_id)

        indicator = await self._indicator_repo.get_by_startup_and_period(
            report_token.startup_id, report_token.month, report_token.year
        )

        return startup, indicator

    async def submit_report(
        self, report_token: ReportToken, data: dict
    ) -> None:
        indicator = await self._indicator_repo.get_by_startup_and_period(
            report_token.startup_id, report_token.month, report_token.year
        )

        if indicator:
            for field, value in data.items():
                setattr(indicator, field, value)
            await self._indicator_repo.update(indicator)
        else:
            new_indicator = MonthlyIndicator(
                startup_id=report_token.startup_id,
                month=report_token.month,
                year=report_token.year,
                **data,
            )
            await self._indicator_repo.create(new_indicator)
