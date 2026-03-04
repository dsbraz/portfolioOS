from unittest.mock import AsyncMock

import pytest

from app.application.user_invite.list_user_invites import ListUserInvites


@pytest.mark.asyncio
async def test_lists_active_invites():
    repo = AsyncMock()
    repo.get_all_active.return_value = ([], 0)
    use_case = ListUserInvites(repo)

    items, total = await use_case.execute()

    assert items == []
    assert total == 0
    repo.get_all_active.assert_awaited_once()
