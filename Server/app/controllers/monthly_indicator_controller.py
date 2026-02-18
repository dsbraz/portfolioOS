import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.schemas.monthly_indicator import (
    MonthlyIndicatorCreate,
    MonthlyIndicatorListResponse,
    MonthlyIndicatorResponse,
    MonthlyIndicatorUpdate,
)
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository
from app.repositories.startup_repository import StartupRepository
from app.services.monthly_indicator_service import MonthlyIndicatorService

router = APIRouter(prefix="/startups/{startup_id}/indicators", tags=["Monthly Indicators"])


def _get_service(session: AsyncSession = Depends(get_session)) -> MonthlyIndicatorService:
    return MonthlyIndicatorService(MonthlyIndicatorRepository(session))


def _get_startup_repo(session: AsyncSession = Depends(get_session)) -> StartupRepository:
    return StartupRepository(session)


async def _verify_startup_exists(
    startup_id: uuid.UUID,
    startup_repo: StartupRepository = Depends(_get_startup_repo),
) -> uuid.UUID:
    startup = await startup_repo.get_by_id(startup_id)
    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Startup com id {startup_id} não encontrada",
        )
    return startup_id


@router.get("", response_model=MonthlyIndicatorListResponse)
async def list_indicators(
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    service: MonthlyIndicatorService = Depends(_get_service),
):
    items, total = await service.list_indicators(startup_id)
    return MonthlyIndicatorListResponse(
        items=[MonthlyIndicatorResponse.model_validate(i) for i in items],
        total=total,
    )


@router.post(
    "", response_model=MonthlyIndicatorResponse, status_code=status.HTTP_201_CREATED
)
async def create_indicator(
    data: MonthlyIndicatorCreate,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    service: MonthlyIndicatorService = Depends(_get_service),
):
    indicator = MonthlyIndicator(startup_id=startup_id, **data.model_dump())
    created = await service.create_indicator(indicator)
    return MonthlyIndicatorResponse.model_validate(created)


@router.get("/{indicator_id}", response_model=MonthlyIndicatorResponse)
async def get_indicator(
    indicator_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    service: MonthlyIndicatorService = Depends(_get_service),
):
    indicator = await service.get_indicator(indicator_id)
    if not indicator or indicator.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicador com id {indicator_id} não encontrado",
        )
    return MonthlyIndicatorResponse.model_validate(indicator)


@router.patch("/{indicator_id}", response_model=MonthlyIndicatorResponse)
async def update_indicator(
    indicator_id: uuid.UUID,
    data: MonthlyIndicatorUpdate,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    service: MonthlyIndicatorService = Depends(_get_service),
):
    indicator = await service.get_indicator(indicator_id)
    if not indicator or indicator.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicador com id {indicator_id} não encontrado",
        )
    updated = await service.update_indicator(indicator, data.model_dump(exclude_unset=True))
    return MonthlyIndicatorResponse.model_validate(updated)


@router.delete("/{indicator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_indicator(
    indicator_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    service: MonthlyIndicatorService = Depends(_get_service),
):
    indicator = await service.get_indicator(indicator_id)
    if not indicator or indicator.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicador com id {indicator_id} não encontrado",
        )
    await service.delete_indicator(indicator)
