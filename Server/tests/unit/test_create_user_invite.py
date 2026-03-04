from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.user_invite.create_user_invite import (
    CreateUserInvite,
    INVITE_TTL_HOURS,
)
from app.domain.exceptions import ConflictError


@pytest.fixture
def invite_repo():
    mock = AsyncMock()
    mock.get_active_by_email.return_value = None
    mock.create.side_effect = lambda invite: invite
    return mock


@pytest.fixture
def user_repo():
    mock = AsyncMock()
    mock.get_by_email.return_value = None
    return mock


@pytest.fixture
def use_case(invite_repo, user_repo):
    return CreateUserInvite(
        invite_repository=invite_repo,
        user_repository=user_repo,
    )


@pytest.mark.asyncio
async def test_creates_invite_successfully(use_case, invite_repo):
    result = await use_case.execute("invitee@example.com")

    assert result.email == "invitee@example.com"
    assert result.used_at is None
    ttl = result.expires_at - datetime.now(UTC)
    assert ttl.total_seconds() > 0
    assert ttl.total_seconds() <= INVITE_TTL_HOURS * 3600 + 1
    invite_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_raises_conflict_when_email_already_exists(use_case, user_repo):
    user_repo.get_by_email.return_value = MagicMock()

    with pytest.raises(ConflictError, match="Email"):
        await use_case.execute("invitee@example.com")


@pytest.mark.asyncio
async def test_revokes_previous_active_invite(
    use_case, invite_repo
):
    active = MagicMock()
    invite_repo.get_active_by_email.return_value = active

    await use_case.execute("invitee@example.com")

    invite_repo.revoke.assert_awaited_once()
