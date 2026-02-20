from app.domain.models.board_meeting import BoardMeeting
from app.repositories.board_meeting_repository import BoardMeetingRepository


class UpdateBoardMeeting:
    def __init__(self, repository: BoardMeetingRepository) -> None:
        self._repository = repository

    async def execute(self, meeting: BoardMeeting, updates: dict) -> BoardMeeting:
        for field, value in updates.items():
            setattr(meeting, field, value)
        return await self._repository.update(meeting)
