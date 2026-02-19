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
from app.services.report_token_service import ReportTokenService

router = APIRouter(tags=["Public Reports"])


def _get_service(
    session: AsyncSession = Depends(get_session),
) -> ReportTokenService:
    return ReportTokenService(
        ReportTokenRepository(session),
        StartupRepository(session),
        MonthlyIndicatorRepository(session),
    )


@router.get(
    "/report/{token}",
    response_model=ReportFormContext,
)
async def get_form_context(
    token: uuid.UUID,
    service: ReportTokenService = Depends(_get_service),
):
    report_token = await service.get_token_by_value(token)
    if not report_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token invalido ou expirado",
        )

    startup, indicator = await service.get_form_context(report_token)
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
    service: ReportTokenService = Depends(_get_service),
):
    report_token = await service.get_token_by_value(token)
    if not report_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token invalido ou expirado",
        )
    await service.submit_report(report_token, data.model_dump())
