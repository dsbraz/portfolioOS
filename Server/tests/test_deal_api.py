import pytest


@pytest.mark.asyncio
async def test_list_deals_empty(client):
    resp = await client.get("/api/deals")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_deal(client):
    resp = await client.post(
        "/api/deals",
        json={
            "company": "TechCo",
            "sector": "SaaS",
            "stage": "Seed",
            "founders": "Joao e Maria",
            "column": "novo",
            "notes": "Empresa promissora",
            "next_step": "Agendar reuniao",
            "internal_owner": "Carlos",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["company"] == "TechCo"
    assert data["column"] == "novo"
    assert data["sector"] == "SaaS"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_deal_required_fields_only(client):
    resp = await client.post(
        "/api/deals",
        json={"company": "MinimalCo"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["company"] == "MinimalCo"
    assert data["column"] == "novo"
    assert data["sector"] is None


@pytest.mark.asyncio
async def test_get_deal(client):
    create_resp = await client.post(
        "/api/deals",
        json={"company": "GetCo", "sector": "Fintech"},
    )
    deal_id = create_resp.json()["id"]

    resp = await client.get(f"/api/deals/{deal_id}")
    assert resp.status_code == 200
    assert resp.json()["company"] == "GetCo"


@pytest.mark.asyncio
async def test_update_deal(client):
    create_resp = await client.post(
        "/api/deals",
        json={"company": "UpdateCo"},
    )
    deal_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/deals/{deal_id}",
        json={"sector": "HealthTech", "notes": "Atualizado"},
    )
    assert resp.status_code == 200
    assert resp.json()["sector"] == "HealthTech"
    assert resp.json()["notes"] == "Atualizado"


@pytest.mark.asyncio
async def test_move_deal(client):
    create_resp = await client.post(
        "/api/deals",
        json={"company": "MoveCo"},
    )
    deal_id = create_resp.json()["id"]
    assert create_resp.json()["column"] == "novo"

    resp = await client.patch(
        f"/api/deals/{deal_id}/move",
        json={"column": "conversando", "position": 1},
    )
    assert resp.status_code == 200
    assert resp.json()["column"] == "conversando"
    assert resp.json()["position"] == 1


@pytest.mark.asyncio
async def test_delete_deal(client):
    create_resp = await client.post(
        "/api/deals",
        json={"company": "DeleteCo"},
    )
    deal_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/deals/{deal_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/deals/{deal_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_deal_not_found(client):
    fake_id = "00000000-0000-0000-0000-000000000001"
    resp = await client.get(f"/api/deals/{fake_id}")
    assert resp.status_code == 404
