import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.domain.schemas.report_token import (
    ReportTokenCreate,
    ReportTokenListResponse,
    ReportTokenResponse,
)
from app.repositories.report_token_repository import ReportTokenRepository
from app.repositories.startup_repository import StartupRepository
from app.application.report_token.generate_report_token import GenerateReportToken

router = APIRouter(tags=["Report Tokens"])


def _get_token_repo(
    session: AsyncSession = Depends(get_session),
) -> ReportTokenRepository:
    return ReportTokenRepository(session)


def _get_generate_use_case(
    token_repo: ReportTokenRepository = Depends(_get_token_repo),
) -> GenerateReportToken:
    return GenerateReportToken(token_repo)


async def _verify_startup_exists(
    startup_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> uuid.UUID:
    startup = await StartupRepository(session).get_by_id(startup_id)
    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Startup com id {startup_id} nao encontrada",
        )
    return startup_id


# --- Admin routes ---


@router.post(
    "/startups/{startup_id}/report-tokens",
    response_model=ReportTokenResponse,
    status_code=status.HTTP_200_OK,
)
async def generate_token(
    data: ReportTokenCreate,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    generate: GenerateReportToken = Depends(_get_generate_use_case),
):
    try:
        token = await generate.execute(startup_id, data.month, data.year)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return ReportTokenResponse.model_validate(token)


@router.get(
    "/startups/{startup_id}/report-tokens",
    response_model=ReportTokenListResponse,
)
async def list_tokens(
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    token_repo: ReportTokenRepository = Depends(_get_token_repo),
):
    items, total = await token_repo.get_all_by_startup(startup_id)
    return ReportTokenListResponse(
        items=[ReportTokenResponse.model_validate(t) for t in items],
        total=total,
    )
