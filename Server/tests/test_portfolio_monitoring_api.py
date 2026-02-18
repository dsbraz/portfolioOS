import pytest


@pytest.mark.asyncio
async def test_monitoring_summary_empty(client):
    resp = await client.get("/api/portfolio-monitoring/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_startups"] == 0
    assert float(data["portfolio_revenue"]) == 0
    assert data["portfolio_health"] == {"healthy": 0, "warning": 0, "critical": 0}
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

    resp = await client.get("/api/portfolio-monitoring/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_startups"] == 2
    assert data["portfolio_health"]["healthy"] == 1
    assert data["portfolio_health"]["warning"] == 1
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
        f"/api/startups/{startup_id}/indicators",
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
        f"/api/startups/{startup_id}/indicators",
        json={
            "month": 2,
            "year": 2026,
            "total_revenue": 120000,
            "cash_balance": 480000,
            "ebitda_burn": -15000,
            "headcount": 18,
        },
    )

    resp = await client.get("/api/portfolio-monitoring/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["portfolio_revenue"]) == 120000
    startup_item = data["startups"][0]
    assert float(startup_item["total_revenue"]) == 120000
    assert startup_item["headcount"] == 18


@pytest.mark.asyncio
async def test_monitoring_summary_health_distribution(client):
    await client.post(
        "/api/startups",
        json={
            "name": "Healthy",
            "sector": "tech",
            "investment_date": "2025-01-01",
            "status": "saudavel",
        },
    )
    await client.post(
        "/api/startups",
        json={
            "name": "Warning",
            "sector": "fintech",
            "investment_date": "2025-01-01",
            "status": "atencao",
        },
    )
    await client.post(
        "/api/startups",
        json={
            "name": "Critical",
            "sector": "biotech",
            "investment_date": "2025-01-01",
            "status": "critico",
        },
    )

    resp = await client.get("/api/portfolio-monitoring/summary")
    data = resp.json()
    assert data["portfolio_health"]["healthy"] == 1
    assert data["portfolio_health"]["warning"] == 1
    assert data["portfolio_health"]["critical"] == 1
