from app.domain.models.board_meeting import BoardMeeting
from app.domain.repositories import BoardMeetingRepository


class DeleteBoardMeeting:
    def __init__(self, repository: BoardMeetingRepository) -> None:
        self._repository = repository

    async def execute(self, meeting: BoardMeeting) -> None:
        await self._repository.delete(meeting)
