from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.user.register_user import RegisterUser
from app.domain.exceptions import ConflictError


@pytest.fixture
def repo():
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
def use_case(repo, hasher):
    return RegisterUser(repository=repo, password_hasher=hasher)


@pytest.mark.asyncio
async def test_creates_user_successfully(use_case, repo, hasher):
    result = await use_case.execute("newuser", "new@example.com", "password123")

    assert result.username == "newuser"
    assert result.email == "new@example.com"
    assert result.hashed_password == "hashed_pw"
    hasher.hash.assert_called_once_with("password123")
    repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_raises_conflict_on_duplicate_username(use_case, repo):
    repo.get_by_username.return_value = MagicMock()

    with pytest.raises(ConflictError, match="Username"):
        await use_case.execute("existing", "new@example.com", "password123")


@pytest.mark.asyncio
async def test_raises_conflict_on_duplicate_email(use_case, repo):
    repo.get_by_email.return_value = MagicMock()

    with pytest.raises(ConflictError, match="Email"):
        await use_case.execute("newuser", "existing@example.com", "password123")
