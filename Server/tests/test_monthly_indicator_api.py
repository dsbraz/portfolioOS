import pytest


@pytest.mark.asyncio
async def test_list_indicators_empty(client):
    startup_resp = await client.post(
        "/api/startups",
        json={
            "name": "Test Startup",
            "sector": "tech",
            "investment_date": "2026-01-15",
        },
    )
    startup_id = startup_resp.json()["id"]

    resp = await client.get(f"/api/startups/{startup_id}/indicators")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_indicator(client):
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
        f"/api/startups/{startup_id}/indicators",
        json={
            "month": 2,
            "year": 2026,
            "total_revenue": 150000.50,
            "recurring_revenue_pct": 80.5,
            "gross_margin_pct": 65.0,
            "cash_balance": 500000.00,
            "headcount": 25,
            "ebitda_burn": -30000.00,
            "achievements": "Fechamos 3 novos clientes",
            "challenges": "Churn elevado",
            "comments": "Bom mes no geral",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["month"] == 2
    assert data["year"] == 2026
    assert float(data["total_revenue"]) == 150000.50
    assert data["headcount"] == 25
    assert data["startup_id"] == startup_id
    assert "id" in data


@pytest.mark.asyncio
async def test_create_indicator_required_fields_only(client):
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
        f"/api/startups/{startup_id}/indicators",
        json={"month": 1, "year": 2026},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["month"] == 1
    assert data["year"] == 2026
    assert data["total_revenue"] is None


@pytest.mark.asyncio
async def test_create_indicator_duplicate_month(client):
    startup_resp = await client.post(
        "/api/startups",
        json={
            "name": "Test Startup",
            "sector": "tech",
            "investment_date": "2026-01-15",
        },
    )
    startup_id = startup_resp.json()["id"]

    await client.post(
        f"/api/startups/{startup_id}/indicators",
        json={"month": 2, "year": 2026},
    )
    resp = await client.post(
        f"/api/startups/{startup_id}/indicators",
        json={"month": 2, "year": 2026},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_indicator(client):
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
        f"/api/startups/{startup_id}/indicators",
        json={"month": 3, "year": 2026, "headcount": 10},
    )
    indicator_id = create_resp.json()["id"]

    resp = await client.get(f"/api/startups/{startup_id}/indicators/{indicator_id}")
    assert resp.status_code == 200
    assert resp.json()["headcount"] == 10


@pytest.mark.asyncio
async def test_update_indicator(client):
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
        f"/api/startups/{startup_id}/indicators",
        json={"month": 4, "year": 2026, "headcount": 10},
    )
    indicator_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/startups/{startup_id}/indicators/{indicator_id}",
        json={"headcount": 15, "achievements": "Novo produto lancado"},
    )
    assert resp.status_code == 200
    assert resp.json()["headcount"] == 15
    assert resp.json()["achievements"] == "Novo produto lancado"


@pytest.mark.asyncio
async def test_delete_indicator(client):
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
        f"/api/startups/{startup_id}/indicators",
        json={"month": 5, "year": 2026},
    )
    indicator_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/startups/{startup_id}/indicators/{indicator_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/startups/{startup_id}/indicators/{indicator_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_indicator_startup_not_found(client):
    fake_id = "00000000-0000-0000-0000-000000000001"
    resp = await client.get(f"/api/startups/{fake_id}/indicators")
    assert resp.status_code == 404
