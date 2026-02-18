import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_startups_empty(client: AsyncClient):
    response = await client.get("/api/startups")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_startup(client: AsyncClient):
    payload = {
        "name": "TechCorp",
        "site": "https://techcorp.com",
        "logo_url": "https://techcorp.com/logo.png",
        "status": "saudavel",
        "sector": "Tecnologia",
        "investment_date": "2024-06-15",
        "notes": "Promising startup",
    }
    response = await client.post("/api/startups", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "TechCorp"
    assert data["status"] == "saudavel"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_startup_required_fields_only(client: AsyncClient):
    payload = {
        "name": "MinimalCorp",
        "sector": "Fintech",
        "investment_date": "2025-01-10",
    }
    response = await client.post("/api/startups", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "MinimalCorp"
    assert data["status"] == "saudavel"
    assert data["site"] is None


@pytest.mark.asyncio
async def test_create_startup_validation_error(client: AsyncClient):
    payload = {"sector": "Fintech"}
    response = await client.post("/api/startups", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_startup(client: AsyncClient):
    payload = {
        "name": "GetCorp",
        "sector": "Saude",
        "investment_date": "2024-03-20",
    }
    create_resp = await client.post("/api/startups", json=payload)
    startup_id = create_resp.json()["id"]

    response = await client.get(f"/api/startups/{startup_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "GetCorp"


@pytest.mark.asyncio
async def test_get_startup_not_found(client: AsyncClient):
    fake_id = uuid.uuid4()
    response = await client.get(f"/api/startups/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_startup(client: AsyncClient):
    payload = {
        "name": "UpdateCorp",
        "sector": "Educacao",
        "investment_date": "2024-01-01",
    }
    create_resp = await client.post("/api/startups", json=payload)
    startup_id = create_resp.json()["id"]

    update_resp = await client.patch(
        f"/api/startups/{startup_id}",
        json={"status": "critico", "notes": "Needs attention"},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["status"] == "critico"
    assert data["notes"] == "Needs attention"
    assert data["name"] == "UpdateCorp"


@pytest.mark.asyncio
async def test_delete_startup(client: AsyncClient):
    payload = {
        "name": "DeleteCorp",
        "sector": "Logistica",
        "investment_date": "2024-08-01",
    }
    create_resp = await client.post("/api/startups", json=payload)
    startup_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/startups/{startup_id}")
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/api/startups/{startup_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_list_startups_after_creation(client: AsyncClient):
    for i in range(3):
        await client.post(
            "/api/startups",
            json={
                "name": f"Startup{i}",
                "sector": "Tech",
                "investment_date": "2024-01-01",
            },
        )
    response = await client.get("/api/startups")
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
