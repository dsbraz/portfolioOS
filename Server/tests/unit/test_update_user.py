import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.auth.update_user import UpdateUser
from app.domain.exceptions import ConflictError


@pytest.fixture
def repo():
    mock = AsyncMock()
    mock.get_by_username.return_value = None
    mock.get_by_email.return_value = None
    mock.update.side_effect = lambda user: user
    return mock


@pytest.fixture
def hasher():
    mock = MagicMock()
    mock.hash.return_value = "new_hashed_pw"
    return mock


@pytest.fixture
def use_case(repo, hasher):
    return UpdateUser(repository=repo, password_hasher=hasher)


def _make_user(**overrides):
    defaults = {
        "id": uuid.uuid4(),
        "username": "original",
        "email": "original@example.com",
        "hashed_password": "old_hashed",
        "is_active": True,
    }
    defaults.update(overrides)
    user = MagicMock(**defaults)
    user.id = defaults["id"]
    user.username = defaults["username"]
    user.email = defaults["email"]
    return user


@pytest.mark.asyncio
async def test_raises_error_on_self_deactivation(use_case):
    user_id = uuid.uuid4()
    user = _make_user(id=user_id)

    with pytest.raises(ValueError, match="proprio"):
        await use_case.execute(user, {"is_active": False}, current_user_id=user_id)


@pytest.mark.asyncio
async def test_allows_deactivating_other_user(use_case, repo):
    user = _make_user()

    result = await use_case.execute(
        user, {"is_active": False}, current_user_id=uuid.uuid4()
    )

    assert result is user
    repo.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_hashes_new_password(use_case, hasher):
    user = _make_user()

    await use_case.execute(user, {"password": "newpass123"})

    hasher.hash.assert_called_once_with("newpass123")
    assert user.hashed_password == "new_hashed_pw"


@pytest.mark.asyncio
async def test_raises_conflict_on_duplicate_username(use_case, repo):
    user = _make_user()
    repo.get_by_username.return_value = MagicMock()

    with pytest.raises(ConflictError, match="Username"):
        await use_case.execute(user, {"username": "taken"})


@pytest.mark.asyncio
async def test_raises_conflict_on_duplicate_email(use_case, repo):
    user = _make_user()
    repo.get_by_email.return_value = MagicMock()

    with pytest.raises(ConflictError, match="Email"):
        await use_case.execute(user, {"email": "taken@example.com"})


@pytest.mark.asyncio
async def test_skips_uniqueness_check_when_unchanged(use_case, repo):
    user = _make_user(username="same", email="same@example.com")

    await use_case.execute(user, {"username": "same", "email": "same@example.com"})

    repo.get_by_username.assert_not_awaited()
    repo.get_by_email.assert_not_awaited()
