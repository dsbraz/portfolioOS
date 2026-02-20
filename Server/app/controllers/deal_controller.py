import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.deal.create_deal import CreateDeal
from app.application.deal.delete_deal import DeleteDeal
from app.application.deal.get_deal import GetDeal
from app.application.deal.list_deals import ListDeals
from app.application.deal.move_deal import MoveDeal
from app.application.deal.update_deal import UpdateDeal
from app.controllers.dependencies import deal_builder
from app.domain.models.deal import Deal
from app.domain.schemas.deal import (
    DealCreate,
    DealListResponse,
    DealMoveRequest,
    DealResponse,
    DealUpdate,
)

router = APIRouter(prefix="/deals", tags=["Deals"])


@router.get("", response_model=DealListResponse)
async def list_deals(
    use_case: ListDeals = Depends(deal_builder(ListDeals)),
):
    items, total = await use_case.execute()
    return DealListResponse(
        items=[DealResponse.model_validate(d) for d in items],
        total=total,
    )


@router.post("", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    data: DealCreate,
    use_case: CreateDeal = Depends(deal_builder(CreateDeal)),
):
    deal = Deal(**data.model_dump())
    created = await use_case.execute(deal)
    return DealResponse.model_validate(created)


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: uuid.UUID,
    use_case: GetDeal = Depends(deal_builder(GetDeal)),
):
    deal = await use_case.execute(deal_id)
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
    get_uc: GetDeal = Depends(deal_builder(GetDeal)),
    update_uc: UpdateDeal = Depends(deal_builder(UpdateDeal)),
):
    deal = await get_uc.execute(deal_id)
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal com id {deal_id} não encontrado",
        )
    updated = await update_uc.execute(deal, data.model_dump(exclude_unset=True))
    return DealResponse.model_validate(updated)


@router.patch("/{deal_id}/move", response_model=DealResponse)
async def move_deal(
    deal_id: uuid.UUID,
    data: DealMoveRequest,
    get_uc: GetDeal = Depends(deal_builder(GetDeal)),
    move_uc: MoveDeal = Depends(deal_builder(MoveDeal)),
):
    deal = await get_uc.execute(deal_id)
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal com id {deal_id} não encontrado",
        )
    moved = await move_uc.execute(deal, data.column, data.position)
    return DealResponse.model_validate(moved)


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: uuid.UUID,
    get_uc: GetDeal = Depends(deal_builder(GetDeal)),
    delete_uc: DeleteDeal = Depends(deal_builder(DeleteDeal)),
):
    deal = await get_uc.execute(deal_id)
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal com id {deal_id} não encontrado",
        )
    await delete_uc.execute(deal)
