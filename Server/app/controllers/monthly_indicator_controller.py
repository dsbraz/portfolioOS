import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.monthly_indicator.create_monthly_indicator import (
    CreateMonthlyIndicator,
)
from app.application.monthly_indicator.delete_monthly_indicator import (
    DeleteMonthlyIndicator,
)
from app.application.monthly_indicator.get_monthly_indicator import GetMonthlyIndicator
from app.application.monthly_indicator.list_monthly_indicators import (
    ListMonthlyIndicators,
)
from app.application.monthly_indicator.update_monthly_indicator import (
    UpdateMonthlyIndicator,
)
from app.controllers.dependencies import monthly_indicator_builder, verify_startup_exists
from app.domain.exceptions import ConflictError
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.schemas.monthly_indicator import (
    MonthlyIndicatorCreate,
    MonthlyIndicatorListResponse,
    MonthlyIndicatorResponse,
    MonthlyIndicatorUpdate,
)

router = APIRouter(prefix="/startups/{startup_id}/indicators", tags=["Monthly Indicators"])


@router.get("", response_model=MonthlyIndicatorListResponse)
async def list_indicators(
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    use_case: ListMonthlyIndicators = Depends(monthly_indicator_builder(ListMonthlyIndicators)),
):
    items, total = await use_case.execute(startup_id)
    return MonthlyIndicatorListResponse(
        items=[MonthlyIndicatorResponse.model_validate(i) for i in items],
        total=total,
    )


@router.post(
    "", response_model=MonthlyIndicatorResponse, status_code=status.HTTP_201_CREATED
)
async def create_indicator(
    data: MonthlyIndicatorCreate,
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    use_case: CreateMonthlyIndicator = Depends(monthly_indicator_builder(CreateMonthlyIndicator)),
):
    indicator = MonthlyIndicator(startup_id=startup_id, **data.model_dump())
    try:
        created = await use_case.execute(indicator)
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
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    use_case: GetMonthlyIndicator = Depends(monthly_indicator_builder(GetMonthlyIndicator)),
):
    indicator = await use_case.execute(indicator_id)
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
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    get_uc: GetMonthlyIndicator = Depends(monthly_indicator_builder(GetMonthlyIndicator)),
    update_uc: UpdateMonthlyIndicator = Depends(monthly_indicator_builder(UpdateMonthlyIndicator)),
):
    indicator = await get_uc.execute(indicator_id)
    if not indicator or indicator.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicador com id {indicator_id} não encontrado",
        )
    try:
        updated = await update_uc.execute(
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
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    get_uc: GetMonthlyIndicator = Depends(monthly_indicator_builder(GetMonthlyIndicator)),
    delete_uc: DeleteMonthlyIndicator = Depends(monthly_indicator_builder(DeleteMonthlyIndicator)),
):
    indicator = await get_uc.execute(indicator_id)
    if not indicator or indicator.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicador com id {indicator_id} não encontrado",
        )
    await delete_uc.execute(indicator)
