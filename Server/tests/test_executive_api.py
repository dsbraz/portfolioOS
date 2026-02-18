import pytest


@pytest.mark.asyncio
async def test_list_executives_empty(client):
    startup_resp = await client.post(
        "/api/startups",
        json={
            "name": "Test Startup",
            "sector": "tech",
            "investment_date": "2026-01-15",
        },
    )
    startup_id = startup_resp.json()["id"]

    resp = await client.get(f"/api/startups/{startup_id}/executives")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_executive(client):
    startup_resp = await client.post(
        "/api/startups",
        json={
            "name": "Test Startup",
            "sector": "tech",
            "investment_date": "2026-01-15",
        },
    )
    startup_id = startup_resp.json()["id"]

    resp = await client.post(
        f"/api/startups/{startup_id}/executives",
        json={
            "name": "Maria Silva",
            "role": "CEO",
            "email": "maria@startup.com",
            "phone": "+55 11 99999-0000",
            "linkedin": "https://linkedin.com/in/mariasilva",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Maria Silva"
    assert data["role"] == "CEO"
    assert data["email"] == "maria@startup.com"
    assert data["startup_id"] == startup_id
    assert "id" in data


@pytest.mark.asyncio
async def test_create_executive_required_fields_only(client):
    startup_resp = await client.post(
        "/api/startups",
        json={
            "name": "Test Startup",
            "sector": "tech",
            "investment_date": "2026-01-15",
        },
    )
    startup_id = startup_resp.json()["id"]

    resp = await client.post(
        f"/api/startups/{startup_id}/executives",
        json={"name": "Joao Santos"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Joao Santos"
    assert data["role"] is None
    assert data["email"] is None


@pytest.mark.asyncio
async def test_get_executive(client):
    startup_resp = await client.post(
        "/api/startups",
        json={
            "name": "Test Startup",
            "sector": "tech",
            "investment_date": "2026-01-15",
        },
    )
    startup_id = startup_resp.json()["id"]

    create_resp = await client.post(
        f"/api/startups/{startup_id}/executives",
        json={"name": "Ana Costa", "role": "CTO"},
    )
    executive_id = create_resp.json()["id"]

    resp = await client.get(f"/api/startups/{startup_id}/executives/{executive_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Ana Costa"
    assert resp.json()["role"] == "CTO"


@pytest.mark.asyncio
async def test_update_executive(client):
    startup_resp = await client.post(
        "/api/startups",
        json={
            "name": "Test Startup",
            "sector": "tech",
            "investment_date": "2026-01-15",
        },
    )
    startup_id = startup_resp.json()["id"]

    create_resp = await client.post(
        f"/api/startups/{startup_id}/executives",
        json={"name": "Pedro Lima", "role": "CFO"},
    )
    executive_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/startups/{startup_id}/executives/{executive_id}",
        json={"role": "COO", "email": "pedro@startup.com"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "COO"
    assert resp.json()["email"] == "pedro@startup.com"
    assert resp.json()["name"] == "Pedro Lima"


@pytest.mark.asyncio
async def test_delete_executive(client):
    startup_resp = await client.post(
        "/api/startups",
        json={
            "name": "Test Startup",
            "sector": "tech",
            "investment_date": "2026-01-15",
        },
    )
    startup_id = startup_resp.json()["id"]

    create_resp = await client.post(
        f"/api/startups/{startup_id}/executives",
        json={"name": "Carlos Souza"},
    )
    executive_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/startups/{startup_id}/executives/{executive_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/startups/{startup_id}/executives/{executive_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_executive_startup_not_found(client):
    fake_id = "00000000-0000-0000-0000-000000000001"
    resp = await client.get(f"/api/startups/{fake_id}/executives")
    assert resp.status_code == 404
