from unittest.mock import MagicMock

import pytest

from app.application.skill.get_skill_pack import GetSkillPack


@pytest.mark.asyncio
async def test_get_skill_pack_returns_repository_package():
    repository = MagicMock()
    repository.get_pack.return_value = b"complete-skill-pack"
    use_case = GetSkillPack(repository)

    result = await use_case.execute()

    assert result == b"complete-skill-pack"
    repository.get_pack.assert_called_once_with()
