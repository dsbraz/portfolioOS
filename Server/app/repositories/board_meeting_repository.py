import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.board_meeting import BoardMeeting


class BoardMeetingRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_all_by_startup(
        self, startup_id: uuid.UUID
    ) -> tuple[list[BoardMeeting], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(BoardMeeting)
            .where(BoardMeeting.startup_id == startup_id)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(BoardMeeting)
            .where(BoardMeeting.startup_id == startup_id)
            .order_by(BoardMeeting.meeting_date.desc())
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, meeting_id: uuid.UUID) -> BoardMeeting | None:
        result = await self._session.execute(
            select(BoardMeeting).where(BoardMeeting.id == meeting_id)
        )
        return result.scalar_one_or_none()

    async def create(self, meeting: BoardMeeting) -> BoardMeeting:
        self._session.add(meeting)
        await self._session.flush()
        await self._session.refresh(meeting)
        return meeting

    async def update(self, meeting: BoardMeeting) -> BoardMeeting:
        await self._session.flush()
        await self._session.refresh(meeting)
        return meeting

    async def delete(self, meeting: BoardMeeting) -> None:
        await self._session.delete(meeting)
        await self._session.flush()
