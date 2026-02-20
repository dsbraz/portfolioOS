import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.domain.schemas.report_token import (
    PublicIndicatorData,
    PublicReportSubmit,
    ReportFormContext,
)
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository
from app.repositories.report_token_repository import ReportTokenRepository
from app.repositories.startup_repository import StartupRepository
from app.application.report_token.get_report_form_context import GetReportFormContext
from app.application.report_token.submit_report import SubmitReport

router = APIRouter(tags=["Public Reports"])


def _get_token_repo(
    session: AsyncSession = Depends(get_session),
) -> ReportTokenRepository:
    return ReportTokenRepository(session)


def _get_form_context_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetReportFormContext:
    return GetReportFormContext(
        StartupRepository(session),
        MonthlyIndicatorRepository(session),
    )


def _get_submit_use_case(
    session: AsyncSession = Depends(get_session),
) -> SubmitReport:
    return SubmitReport(MonthlyIndicatorRepository(session))


@router.get(
    "/report/{token}",
    response_model=ReportFormContext,
)
async def get_form_context(
    token: uuid.UUID,
    token_repo: ReportTokenRepository = Depends(_get_token_repo),
    form_context: GetReportFormContext = Depends(_get_form_context_use_case),
):
    report_token = await token_repo.get_by_token(token)
    if not report_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token invalido ou expirado",
        )

    startup, indicator = await form_context.execute(report_token)
    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup nao encontrada",
        )

    existing = None
    if indicator:
        existing = PublicIndicatorData.model_validate(indicator)

    return ReportFormContext(
        startup_name=startup.name,
        startup_logo_url=startup.logo_url,
        month=report_token.month,
        year=report_token.year,
        existing_indicator=existing,
    )


@router.post(
    "/report/{token}/submit",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def submit_report(
    token: uuid.UUID,
    data: PublicReportSubmit,
    token_repo: ReportTokenRepository = Depends(_get_token_repo),
    submit: SubmitReport = Depends(_get_submit_use_case),
):
    report_token = await token_repo.get_by_token(token)
    if not report_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token invalido ou expirado",
        )
    await submit.execute(report_token, data.model_dump())
