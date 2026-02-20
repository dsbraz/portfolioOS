import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.domain.exceptions import ConflictError
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.schemas.monthly_indicator import (
    MonthlyIndicatorCreate,
    MonthlyIndicatorListResponse,
    MonthlyIndicatorResponse,
    MonthlyIndicatorUpdate,
)
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository
from app.repositories.startup_repository import StartupRepository
from app.use_cases.base_crud import CrudUseCase
from app.use_cases.monthly_indicator.create_monthly_indicator import (
    CreateMonthlyIndicator,
)
from app.use_cases.monthly_indicator.update_monthly_indicator import (
    UpdateMonthlyIndicator,
)

router = APIRouter(prefix="/startups/{startup_id}/indicators", tags=["Monthly Indicators"])


def _get_repo(session: AsyncSession = Depends(get_session)) -> MonthlyIndicatorRepository:
    return MonthlyIndicatorRepository(session)


def _get_crud(
    repo: MonthlyIndicatorRepository = Depends(_get_repo),
) -> CrudUseCase[MonthlyIndicator]:
    return CrudUseCase(repo)


def _get_create_use_case(
    repo: MonthlyIndicatorRepository = Depends(_get_repo),
) -> CreateMonthlyIndicator:
    return CreateMonthlyIndicator(repo)


def _get_update_use_case(
    repo: MonthlyIndicatorRepository = Depends(_get_repo),
) -> UpdateMonthlyIndicator:
    return UpdateMonthlyIndicator(repo)


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
    crud: CrudUseCase[MonthlyIndicator] = Depends(_get_crud),
):
    items, total = await crud.list_by_parent(startup_id)
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
    create_use_case: CreateMonthlyIndicator = Depends(_get_create_use_case),
):
    indicator = MonthlyIndicator(startup_id=startup_id, **data.model_dump())
    try:
        created = await create_use_case.execute(indicator)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return MonthlyIndicatorResponse.model_validate(created)


@router.get("/{indicator_id}", response_model=MonthlyIndicatorResponse)
async def get_indicator(
    indicator_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    crud: CrudUseCase[MonthlyIndicator] = Depends(_get_crud),
):
    indicator = await crud.get_by_id(indicator_id)
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
    crud: CrudUseCase[MonthlyIndicator] = Depends(_get_crud),
    update_use_case: UpdateMonthlyIndicator = Depends(_get_update_use_case),
):
    indicator = await crud.get_by_id(indicator_id)
    if not indicator or indicator.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicador com id {indicator_id} não encontrado",
        )
    try:
        updated = await update_use_case.execute(
            indicator, data.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return MonthlyIndicatorResponse.model_validate(updated)


@router.delete("/{indicator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_indicator(
    indicator_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    crud: CrudUseCase[MonthlyIndicator] = Depends(_get_crud),
):
    indicator = await crud.get_by_id(indicator_id)
    if not indicator or indicator.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicador com id {indicator_id} não encontrado",
        )
    await crud.delete(indicator)
