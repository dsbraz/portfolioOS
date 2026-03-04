from datetime import date

import pytest


@pytest.mark.asyncio
async def test_monitoring_summary_empty(client):
    resp = await client.get("/api/portfolio/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_startups"] == 0
    assert float(data["revenue"]) == 0
    assert data["health"] == {"healthy": 0, "warning": 0, "critical": 0}
    assert data["revenue_variation_pct"] is None
    assert data["revenue_variation_direction"] == "neutral"
    assert data["monthly_report_pct"] == 0.0
    assert data["routines_up_to_date_pct"] == 0.0
    assert data["startups"] == []


@pytest.mark.asyncio
async def test_monitoring_summary_with_startups(client):
    await client.post(
        "/api/startups",
        json={
            "name": "Startup Alpha",
            "sector": "tech",
            "investment_date": "2025-06-01",
            "status": "saudavel",
        },
    )
    await client.post(
        "/api/startups",
        json={
            "name": "Startup Beta",
            "sector": "fintech",
            "investment_date": "2025-09-15",
            "status": "atencao",
        },
    )

    resp = await client.get("/api/portfolio/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_startups"] == 2
    assert data["health"]["healthy"] == 1
    assert data["health"]["warning"] == 1
    assert len(data["startups"]) == 2


@pytest.mark.asyncio
async def test_monitoring_summary_with_indicators(client):
    startup_resp = await client.post(
        "/api/startups",
        json={
            "name": "Startup With Data",
            "sector": "saas",
            "investment_date": "2025-01-01",
        },
    )
    startup_id = startup_resp.json()["id"]

    await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={
            "month": 1,
            "year": 2026,
            "total_revenue": 100000,
            "cash_balance": 500000,
            "ebitda_burn": -20000,
            "headcount": 15,
        },
    )
    await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={
            "month": 2,
            "year": 2026,
            "total_revenue": 120000,
            "cash_balance": 480000,
            "ebitda_burn": -15000,
            "headcount": 18,
        },
    )

    resp = await client.get("/api/portfolio/summary?month=2&year=2026")
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["revenue"]) == 120000
    assert data["revenue_variation_pct"] == 20.0
    assert data["revenue_variation_direction"] == "up"
    startup_item = data["startups"][0]
    assert float(startup_item["total_revenue"]) == 120000
    assert startup_item["headcount"] == 18


@pytest.mark.asyncio
async def test_monitoring_summary_revenue_variation_without_base(client):
    startup_resp = await client.post(
        "/api/startups",
        json={
            "name": "Startup No Base",
            "sector": "saas",
            "investment_date": "2025-01-01",
        },
    )
    startup_id = startup_resp.json()["id"]

    await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={
            "month": 2,
            "year": 2026,
            "total_revenue": 90000,
            "cash_balance": 300000,
            "ebitda_burn": -10000,
            "headcount": 12,
        },
    )

    resp = await client.get("/api/portfolio/summary?month=2&year=2026")
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["revenue"]) == 90000
    assert data["revenue_variation_pct"] is None
    assert data["revenue_variation_direction"] == "neutral"


@pytest.mark.asyncio
async def test_monitoring_summary_should_return_400_with_partial_period(client):
    resp = await client.get("/api/portfolio/summary?month=1")
    assert resp.status_code == 400
    assert "Mes e ano devem ser informados juntos" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_monitoring_summary_should_return_400_with_future_period(client):
    today = date.today()
    future_month = 1 if today.month == 12 else today.month + 1
    future_year = today.year + 1 if today.month == 12 else today.year

    resp = await client.get(
        f"/api/portfolio/summary?month={future_month}&year={future_year}"
    )
    assert resp.status_code == 400
    assert "nao pode ser no futuro" in resp.json()["detail"]
