import pytest
from httpx import AsyncClient

from app.controllers.skill_controller import PACK_PATH


@pytest.mark.asyncio
async def test_skill_pack_download_serves_the_committed_zip(anon_client: AsyncClient):
    response = await anon_client.get("/api/skills.zip")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert 'filename="portfolioos.zip"' in response.headers["content-disposition"]
    assert response.content == PACK_PATH.read_bytes()
