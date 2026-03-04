import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.user_invite.consume_user_invite import ConsumeUserInvite
from app.domain.exceptions import ConflictError


@pytest.fixture
def invite_repo():
    return AsyncMock()


@pytest.fixture
def user_repo():
    mock = AsyncMock()
    mock.get_by_username.return_value = None
    mock.get_by_email.return_value = None
    mock.create.side_effect = lambda user: user
    return mock


@pytest.fixture
def hasher():
    mock = MagicMock()
    mock.hash.return_value = "hashed_pw"
    return mock


@pytest.fixture
def use_case(invite_repo, user_repo, hasher):
    return ConsumeUserInvite(
        invite_repository=invite_repo,
        user_repository=user_repo,
        password_hasher=hasher,
    )


def _active_invite(email: str = "invitee@example.com") -> MagicMock:
    now = datetime.now(UTC)
    return MagicMock(
        token=uuid.uuid4(),
        email=email,
        used_at=None,
        expires_at=now + timedelta(hours=1),
    )


@pytest.mark.asyncio
async def test_consumes_invite_and_creates_user(
    use_case, invite_repo, user_repo
):
    invite_repo.get_by_token.return_value = _active_invite()

    result = await use_case.execute(
        uuid.uuid4(), "invitee@example.com", "newuser", "password123"
    )

    assert result.username == "newuser"
    assert result.email == "invitee@example.com"
    user_repo.create.assert_awaited_once()
    invite_repo.mark_used.assert_awaited_once()


@pytest.mark.asyncio
async def test_returns_none_when_invite_not_found(use_case, invite_repo):
    invite_repo.get_by_token.return_value = None

    result = await use_case.execute(
        uuid.uuid4(), "invitee@example.com", "newuser", "password123"
    )

    assert result is None


@pytest.mark.asyncio
async def test_raises_conflict_when_username_exists(
    use_case, invite_repo, user_repo
):
    invite_repo.get_by_token.return_value = _active_invite()
    user_repo.get_by_username.return_value = MagicMock()

    with pytest.raises(ConflictError, match="Username"):
        await use_case.execute(
            uuid.uuid4(), "invitee@example.com", "taken", "password123"
        )


@pytest.mark.asyncio
async def test_raises_value_error_when_email_mismatch(
    use_case, invite_repo
):
    invite_repo.get_by_token.return_value = _active_invite(
        email="expected@example.com"
    )

    with pytest.raises(ValueError, match="Email"):
        await use_case.execute(
            uuid.uuid4(), "other@example.com", "newuser", "password123"
        )


@pytest.mark.asyncio
async def test_raises_value_error_when_username_has_spaces(
    use_case, invite_repo
):
    invite_repo.get_by_token.return_value = _active_invite()

    with pytest.raises(ValueError, match="Username"):
        await use_case.execute(
            uuid.uuid4(), "invitee@example.com", "new user", "password123"
        )
