import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.domain.schemas.report_token import (
    PublicReportSubmit,
    ReportFormContext,
    ReportTokenCreate,
    ReportTokenListResponse,
    ReportTokenResponse,
)
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository
from app.repositories.report_token_repository import ReportTokenRepository
from app.repositories.startup_repository import StartupRepository
from app.services.report_token_service import ReportTokenService

router = APIRouter(tags=["Report Tokens"])


def _get_service(session: AsyncSession = Depends(get_session)) -> ReportTokenService:
    return ReportTokenService(
        ReportTokenRepository(session),
        StartupRepository(session),
        MonthlyIndicatorRepository(session),
    )


# --- Admin routes ---


@router.post(
    "/startups/{startup_id}/report-tokens",
    response_model=ReportTokenResponse,
    status_code=status.HTTP_200_OK,
)
async def generate_token(
    startup_id: uuid.UUID,
    data: ReportTokenCreate,
    service: ReportTokenService = Depends(_get_service),
):
    token = await service.generate_token(startup_id, data.month, data.year)
    return ReportTokenResponse.model_validate(token)


@router.get(
    "/startups/{startup_id}/report-tokens",
    response_model=ReportTokenListResponse,
)
async def list_tokens(
    startup_id: uuid.UUID,
    service: ReportTokenService = Depends(_get_service),
):
    items, total = await service.list_tokens(startup_id)
    return ReportTokenListResponse(
        items=[ReportTokenResponse.model_validate(t) for t in items],
        total=total,
    )


# --- Public routes ---


@router.get(
    "/report/{token}",
    response_model=ReportFormContext,
)
async def get_form_context(
    token: uuid.UUID,
    service: ReportTokenService = Depends(_get_service),
):
    return await service.get_form_context(token)


@router.post(
    "/report/{token}/submit",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def submit_report(
    token: uuid.UUID,
    data: PublicReportSubmit,
    service: ReportTokenService = Depends(_get_service),
):
    await service.submit_report(token, data)
