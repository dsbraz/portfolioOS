import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.monthly_indicator.create_monthly_indicator import (
    CreateMonthlyIndicator,
)
from app.application.monthly_indicator.create_monthly_indicator_token import (
    CreateMonthlyIndicatorToken,
)
from app.application.monthly_indicator.delete_monthly_indicator import (
    DeleteMonthlyIndicator,
)
from app.application.monthly_indicator.get_monthly_indicator import GetMonthlyIndicator
from app.application.monthly_indicator.get_monthly_indicator_token import (
    GetMonthlyIndicatorToken,
)
from app.application.monthly_indicator.get_public_indicator_form import (
    GetPublicIndicatorForm,
)
from app.application.monthly_indicator.list_monthly_indicator_tokens import (
    ListMonthlyIndicatorTokens,
)
from app.application.monthly_indicator.list_monthly_indicators import (
    ListMonthlyIndicators,
)
from app.application.monthly_indicator.update_monthly_indicator import (
    UpdateMonthlyIndicator,
)
from app.controllers.dependencies import (
    monthly_indicator_builder,
    public_form_builder,
    verify_startup_exists,
)
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.schemas.monthly_indicator import (
    MonthlyIndicatorCreate,
    MonthlyIndicatorListResponse,
    MonthlyIndicatorResponse,
    MonthlyIndicatorTokenListResponse,
    MonthlyIndicatorTokenResponse,
    MonthlyIndicatorUpdate,
    PublicIndicatorData,
    PublicIndicatorForm,
    PublicIndicatorSubmit,
)

public_router = APIRouter(tags=["Monthly Indicators"])
router = APIRouter(tags=["Monthly Indicators"])


# --- Public routes (no auth) ---


@public_router.get(
    "/monthly-indicator/{token}",
    response_model=PublicIndicatorForm,
)
async def public_get_monthly_indicator(
    token: uuid.UUID,
    get_token: GetMonthlyIndicatorToken = Depends(
        monthly_indicator_builder(GetMonthlyIndicatorToken)
    ),
    get_form: GetPublicIndicatorForm = Depends(
        public_form_builder(GetPublicIndicatorForm)
    ),
):
    indicator_token = await get_token.execute(token)
    if not indicator_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token invalido ou expirado",
        )

    startup, indicator = await get_form.execute(indicator_token)
    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup nao encontrada",
        )

    existing = None
    if indicator:
        existing = PublicIndicatorData.model_validate(indicator)

    return PublicIndicatorForm(
        startup_name=startup.name,
        startup_logo_url=startup.logo_url,
        month=indicator_token.month,
        year=indicator_token.year,
        existing_indicator=existing,
    )


@public_router.post(
    "/monthly-indicator/{token}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def public_create_monthly_indicator(
    token: uuid.UUID,
    data: PublicIndicatorSubmit,
    get_token: GetMonthlyIndicatorToken = Depends(
        monthly_indicator_builder(GetMonthlyIndicatorToken)
    ),
    create: CreateMonthlyIndicator = Depends(
        monthly_indicator_builder(CreateMonthlyIndicator)
    ),
):
    indicator_token = await get_token.execute(token)
    if not indicator_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token invalido ou expirado",
        )

    indicator = MonthlyIndicator(
        startup_id=indicator_token.startup_id,
        month=indicator_token.month,
        year=indicator_token.year,
        **data.model_dump(),
    )
    await create.execute(indicator)


# --- Protected routes: indicators ---


@router.get(
    "/startups/{startup_id}/monthly-indicators",
    response_model=MonthlyIndicatorListResponse,
)
async def list_indicators(
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    use_case: ListMonthlyIndicators = Depends(
        monthly_indicator_builder(ListMonthlyIndicators)
    ),
):
    items, total = await use_case.execute(startup_id)
    return MonthlyIndicatorListResponse(
        items=[MonthlyIndicatorResponse.model_validate(i) for i in items],
        total=total,
    )


@router.post(
    "/startups/{startup_id}/monthly-indicators",
    response_model=MonthlyIndicatorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_indicator(
    data: MonthlyIndicatorCreate,
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    use_case: CreateMonthlyIndicator = Depends(
        monthly_indicator_builder(CreateMonthlyIndicator)
    ),
):
    indicator = MonthlyIndicator(startup_id=startup_id, **data.model_dump())
    try:
        created = await use_case.execute(indicator)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return MonthlyIndicatorResponse.model_validate(created)


@router.get(
    "/startups/{startup_id}/monthly-indicators/{indicator_id}",
    response_model=MonthlyIndicatorResponse,
)
async def get_indicator(
    indicator_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    use_case: GetMonthlyIndicator = Depends(
        monthly_indicator_builder(GetMonthlyIndicator)
    ),
):
    indicator = await use_case.execute(indicator_id)
    if not indicator or indicator.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicador com id {indicator_id} não encontrado",
        )
    return MonthlyIndicatorResponse.model_validate(indicator)


@router.patch(
    "/startups/{startup_id}/monthly-indicators/{indicator_id}",
    response_model=MonthlyIndicatorResponse,
)
async def update_indicator(
    indicator_id: uuid.UUID,
    data: MonthlyIndicatorUpdate,
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    get_uc: GetMonthlyIndicator = Depends(
        monthly_indicator_builder(GetMonthlyIndicator)
    ),
    update_uc: UpdateMonthlyIndicator = Depends(
        monthly_indicator_builder(UpdateMonthlyIndicator)
    ),
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


@router.delete(
    "/startups/{startup_id}/monthly-indicators/{indicator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_indicator(
    indicator_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    get_uc: GetMonthlyIndicator = Depends(
        monthly_indicator_builder(GetMonthlyIndicator)
    ),
    delete_uc: DeleteMonthlyIndicator = Depends(
        monthly_indicator_builder(DeleteMonthlyIndicator)
    ),
):
    indicator = await get_uc.execute(indicator_id)
    if not indicator or indicator.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicador com id {indicator_id} não encontrado",
        )
    await delete_uc.execute(indicator)


# --- Protected routes: tokens ---


@router.post(
    "/startups/{startup_id}/monthly-indicator-tokens",
    response_model=MonthlyIndicatorTokenResponse,
    status_code=status.HTTP_200_OK,
)
async def create_monthly_indicator_token(
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    create: CreateMonthlyIndicatorToken = Depends(
        monthly_indicator_builder(CreateMonthlyIndicatorToken)
    ),
):
    token = await create.execute(startup_id)
    return MonthlyIndicatorTokenResponse.model_validate(token)


@router.get(
    "/startups/{startup_id}/monthly-indicator-tokens",
    response_model=MonthlyIndicatorTokenListResponse,
)
async def list_monthly_indicator_tokens(
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    list_uc: ListMonthlyIndicatorTokens = Depends(
        monthly_indicator_builder(ListMonthlyIndicatorTokens)
    ),
):
    items, total = await list_uc.execute(startup_id)
    return MonthlyIndicatorTokenListResponse(
        items=[MonthlyIndicatorTokenResponse.model_validate(t) for t in items],
        total=total,
    )
