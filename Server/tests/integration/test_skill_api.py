import pytest
from httpx import AsyncClient

from scripts.build_skill_pack import PACK_PATH


@pytest.mark.asyncio
async def test_skill_pack_is_served_from_the_static_folder(anon_client: AsyncClient):
    response = await anon_client.get("/api/static/portfolioos.zip")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.content == PACK_PATH.read_bytes()
