import uuid
from datetime import date

from fastapi import HTTPException, status

from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.report_token import ReportToken
from app.domain.schemas.report_token import (
    PublicIndicatorData,
    PublicReportSubmit,
    ReportFormContext,
)
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Periodo {month}/{year} nao pode ser no futuro",
            )

    async def generate_token(
        self, startup_id: uuid.UUID, month: int, year: int
    ) -> ReportToken:
        self._validate_period_not_future(month, year)

        startup = await self._startup_repo.get_by_id(startup_id)
        if not startup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Startup com id {startup_id} nao encontrada",
            )

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
        startup = await self._startup_repo.get_by_id(startup_id)
        if not startup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Startup com id {startup_id} nao encontrada",
            )
        return await self._token_repo.get_all_by_startup(startup_id)

    async def get_form_context(self, token: uuid.UUID) -> ReportFormContext:
        report_token = await self._token_repo.get_by_token(token)
        if not report_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token invalido ou expirado",
            )

        startup = await self._startup_repo.get_by_id(report_token.startup_id)
        if not startup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Startup nao encontrada",
            )

        existing = None
        indicator = await self._indicator_repo.get_by_startup_and_period(
            report_token.startup_id, report_token.month, report_token.year
        )
        if indicator:
            existing = PublicIndicatorData(
                total_revenue=indicator.total_revenue,
                cash_balance=indicator.cash_balance,
                ebitda_burn=indicator.ebitda_burn,
                recurring_revenue_pct=indicator.recurring_revenue_pct,
                gross_margin_pct=indicator.gross_margin_pct,
                headcount=indicator.headcount,
                achievements=indicator.achievements,
                challenges=indicator.challenges,
            )

        return ReportFormContext(
            startup_name=startup.name,
            startup_logo_url=startup.logo_url,
            month=report_token.month,
            year=report_token.year,
            existing_indicator=existing,
        )

    async def submit_report(
        self, token: uuid.UUID, data: PublicReportSubmit
    ) -> None:
        report_token = await self._token_repo.get_by_token(token)
        if not report_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token invalido ou expirado",
            )

        indicator = await self._indicator_repo.get_by_startup_and_period(
            report_token.startup_id, report_token.month, report_token.year
        )

        update_fields = data.model_dump()

        if indicator:
            for field, value in update_fields.items():
                setattr(indicator, field, value)
            await self._indicator_repo.update(indicator)
        else:
            new_indicator = MonthlyIndicator(
                startup_id=report_token.startup_id,
                month=report_token.month,
                year=report_token.year,
                **update_fields,
            )
            await self._indicator_repo.create(new_indicator)
