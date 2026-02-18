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
from app.services.deal_service import DealService

router = APIRouter(prefix="/deals", tags=["Deals"])


def _get_service(session: AsyncSession = Depends(get_session)) -> DealService:
    return DealService(DealRepository(session))


@router.get("", response_model=DealListResponse)
async def list_deals(service: DealService = Depends(_get_service)):
    items, total = await service.list_deals()
    return DealListResponse(
        items=[DealResponse.model_validate(d) for d in items],
        total=total,
    )


@router.post("", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    data: DealCreate,
    service: DealService = Depends(_get_service),
):
    deal = Deal(**data.model_dump())
    created = await service.create_deal(deal)
    return DealResponse.model_validate(created)


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: uuid.UUID,
    service: DealService = Depends(_get_service),
):
    deal = await service.get_deal(deal_id)
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
    service: DealService = Depends(_get_service),
):
    deal = await service.get_deal(deal_id)
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal com id {deal_id} não encontrado",
        )
    updated = await service.update_deal(deal, data.model_dump(exclude_unset=True))
    return DealResponse.model_validate(updated)


@router.patch("/{deal_id}/move", response_model=DealResponse)
async def move_deal(
    deal_id: uuid.UUID,
    data: DealMoveRequest,
    service: DealService = Depends(_get_service),
):
    deal = await service.get_deal(deal_id)
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal com id {deal_id} não encontrado",
        )
    moved = await service.move_deal(deal, data.column, data.position)
    return DealResponse.model_validate(moved)


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: uuid.UUID,
    service: DealService = Depends(_get_service),
):
    deal = await service.get_deal(deal_id)
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal com id {deal_id} não encontrado",
        )
    await service.delete_deal(deal)
