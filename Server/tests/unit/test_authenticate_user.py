from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.auth.authenticate_user import AuthenticateUser


@pytest.fixture
def repo():
    return AsyncMock()


@pytest.fixture
def hasher():
    mock = MagicMock()
    mock.verify = MagicMock(return_value=True)
    return mock


@pytest.fixture
def use_case(repo, hasher):
    return AuthenticateUser(repository=repo, password_hasher=hasher)


@pytest.mark.asyncio
async def test_returns_user_on_valid_credentials(use_case, repo, hasher):
    user = MagicMock(hashed_password="hashed", is_active=True)
    repo.get_by_username.return_value = user

    result = await use_case.execute("admin", "password")

    assert result is user
    repo.get_by_username.assert_awaited_once_with("admin")
    hasher.verify.assert_called_once_with("password", "hashed")


@pytest.mark.asyncio
async def test_returns_none_when_user_not_found(use_case, repo):
    repo.get_by_username.return_value = None

    result = await use_case.execute("nobody", "password")

    assert result is None


@pytest.mark.asyncio
async def test_returns_none_on_wrong_password(use_case, repo, hasher):
    user = MagicMock(hashed_password="hashed", is_active=True)
    repo.get_by_username.return_value = user
    hasher.verify.return_value = False

    result = await use_case.execute("admin", "wrong")

    assert result is None


@pytest.mark.asyncio
async def test_returns_none_when_user_inactive(use_case, repo, hasher):
    user = MagicMock(hashed_password="hashed", is_active=False)
    repo.get_by_username.return_value = user

    result = await use_case.execute("admin", "password")

    assert result is None
