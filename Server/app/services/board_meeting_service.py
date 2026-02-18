import uuid

from app.domain.models.board_meeting import BoardMeeting
from app.repositories.board_meeting_repository import BoardMeetingRepository


class BoardMeetingService:
    def __init__(self, repository: BoardMeetingRepository):
        self._repository = repository

    async def list_meetings(
        self, startup_id: uuid.UUID
    ) -> tuple[list[BoardMeeting], int]:
        return await self._repository.get_all_by_startup(startup_id)

    async def get_meeting(self, meeting_id: uuid.UUID) -> BoardMeeting | None:
        return await self._repository.get_by_id(meeting_id)

    async def create_meeting(self, meeting: BoardMeeting) -> BoardMeeting:
        return await self._repository.create(meeting)

    async def update_meeting(
        self, meeting: BoardMeeting, updates: dict
    ) -> BoardMeeting:
        for field, value in updates.items():
            setattr(meeting, field, value)
        return await self._repository.update(meeting)

    async def delete_meeting(self, meeting: BoardMeeting) -> None:
        await self._repository.delete(meeting)
