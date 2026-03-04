import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.deal import Deal


class DealRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_all(self) -> tuple[list[Deal], int]:
        count_result = await self._session.execute(
            select(func.count()).select_from(Deal)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(Deal).order_by(Deal.stage, Deal.position, Deal.created_at.desc())
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, deal_id: uuid.UUID) -> Deal | None:
        result = await self._session.execute(select(Deal).where(Deal.id == deal_id))
        return result.scalar_one_or_none()

    async def create(self, deal: Deal) -> Deal:
        self._session.add(deal)
        await self._session.flush()
        await self._session.refresh(deal)
        return deal

    async def update(self, deal: Deal) -> Deal:
        await self._session.flush()
        await self._session.refresh(deal)
        return deal

    async def delete(self, deal: Deal) -> None:
        await self._session.delete(deal)
        await self._session.flush()
