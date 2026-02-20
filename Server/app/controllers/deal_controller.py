import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.domain.models.deal import Deal
from app.domain.schemas.deal import (
    DealCreate,
    DealListResponse,
    DealMoveRequest,
    DealResponse,
    DealUpdate,
)
from app.repositories.deal_repository import DealRepository
from app.use_cases.base_crud import CrudUseCase
from app.use_cases.deal.move_deal import MoveDeal

router = APIRouter(prefix="/deals", tags=["Deals"])


def _get_use_case(
    session: AsyncSession = Depends(get_session),
) -> CrudUseCase[Deal]:
    return CrudUseCase(DealRepository(session))


def _get_move_deal(
    session: AsyncSession = Depends(get_session),
) -> MoveDeal:
    return MoveDeal(DealRepository(session))


@router.get("", response_model=DealListResponse)
async def list_deals(
    use_case: CrudUseCase[Deal] = Depends(_get_use_case),
):
    items, total = await use_case.list_all()
    return DealListResponse(
        items=[DealResponse.model_validate(d) for d in items],
        total=total,
    )


@router.post("", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    data: DealCreate,
    use_case: CrudUseCase[Deal] = Depends(_get_use_case),
):
    deal = Deal(**data.model_dump())
    created = await use_case.create(deal)
    return DealResponse.model_validate(created)


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: uuid.UUID,
    use_case: CrudUseCase[Deal] = Depends(_get_use_case),
):
    deal = await use_case.get_by_id(deal_id)
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal com id {deal_id} não encontrado",
        )
    return DealResponse.model_validate(deal)


@router.patch("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: uuid.UUID,
    data: DealUpdate,
    use_case: CrudUseCase[Deal] = Depends(_get_use_case),
):
    deal = await use_case.get_by_id(deal_id)
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal com id {deal_id} não encontrado",
        )
    updated = await use_case.update(deal, data.model_dump(exclude_unset=True))
    return DealResponse.model_validate(updated)


@router.patch("/{deal_id}/move", response_model=DealResponse)
async def move_deal(
    deal_id: uuid.UUID,
    data: DealMoveRequest,
    use_case: CrudUseCase[Deal] = Depends(_get_use_case),
    move_use_case: MoveDeal = Depends(_get_move_deal),
):
    deal = await use_case.get_by_id(deal_id)
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal com id {deal_id} não encontrado",
        )
    moved = await move_use_case.execute(deal, data.column, data.position)
    return DealResponse.model_validate(moved)


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: uuid.UUID,
    use_case: CrudUseCase[Deal] = Depends(_get_use_case),
):
    deal = await use_case.get_by_id(deal_id)
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal com id {deal_id} não encontrado",
        )
    await use_case.delete(deal)
