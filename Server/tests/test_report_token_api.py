import pytest


@pytest.mark.asyncio
async def test_generate_token_creates_new(client):
    startup_resp = await client.post(
        "/api/startups",
        json={"name": "Report Startup", "sector": "tech", "investment_date": "2025-01-01"},
    )
    startup_id = startup_resp.json()["id"]

    resp = await client.post(
        f"/api/startups/{startup_id}/report-tokens",
        json={"month": 1, "year": 2025},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["month"] == 1
    assert data["year"] == 2025
    assert data["startup_id"] == startup_id
    assert "token" in data


@pytest.mark.asyncio
async def test_generate_token_is_idempotent(client):
    startup_resp = await client.post(
        "/api/startups",
        json={"name": "Report Startup", "sector": "tech", "investment_date": "2025-01-01"},
    )
    startup_id = startup_resp.json()["id"]

    resp1 = await client.post(
        f"/api/startups/{startup_id}/report-tokens",
        json={"month": 2, "year": 2025},
    )
    resp2 = await client.post(
        f"/api/startups/{startup_id}/report-tokens",
        json={"month": 2, "year": 2025},
    )
    assert resp1.json()["token"] == resp2.json()["token"]


@pytest.mark.asyncio
async def test_list_tokens(client):
    startup_resp = await client.post(
        "/api/startups",
        json={"name": "Report Startup", "sector": "tech", "investment_date": "2025-01-01"},
    )
    startup_id = startup_resp.json()["id"]

    await client.post(
        f"/api/startups/{startup_id}/report-tokens",
        json={"month": 1, "year": 2025},
    )
    await client.post(
        f"/api/startups/{startup_id}/report-tokens",
        json={"month": 2, "year": 2025},
    )

    resp = await client.get(f"/api/startups/{startup_id}/report-tokens")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_form_context_no_existing_indicator(client):
    startup_resp = await client.post(
        "/api/startups",
        json={"name": "Acme", "sector": "fintech", "investment_date": "2025-01-01"},
    )
    startup_id = startup_resp.json()["id"]

    token_resp = await client.post(
        f"/api/startups/{startup_id}/report-tokens",
        json={"month": 3, "year": 2025},
    )
    token = token_resp.json()["token"]

    resp = await client.get(f"/api/report/{token}")
    assert resp.status_code == 200
    ctx = resp.json()
    assert ctx["startup_name"] == "Acme"
    assert ctx["month"] == 3
    assert ctx["year"] == 2025
    assert ctx["existing_indicator"] is None


@pytest.mark.asyncio
async def test_submit_report_creates_indicator(client):
    startup_resp = await client.post(
        "/api/startups",
        json={"name": "Acme", "sector": "fintech", "investment_date": "2025-01-01"},
    )
    startup_id = startup_resp.json()["id"]

    token_resp = await client.post(
        f"/api/startups/{startup_id}/report-tokens",
        json={"month": 4, "year": 2025},
    )
    token = token_resp.json()["token"]

    resp = await client.post(
        f"/api/report/{token}/submit",
        json={
            "total_revenue": 100000,
            "cash_balance": 500000,
            "ebitda_burn": -20000,
            "headcount": 10,
            "achievements": "Produto lancado",
            "challenges": "Escalar vendas",
        },
    )
    assert resp.status_code == 204

    indicators_resp = await client.get(f"/api/startups/{startup_id}/indicators")
    items = indicators_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["month"] == 4
    assert float(items[0]["total_revenue"]) == 100000.0


@pytest.mark.asyncio
async def test_submit_report_updates_existing_indicator(client):
    startup_resp = await client.post(
        "/api/startups",
        json={"name": "Acme", "sector": "fintech", "investment_date": "2025-01-01"},
    )
    startup_id = startup_resp.json()["id"]

    await client.post(
        f"/api/startups/{startup_id}/indicators",
        json={"month": 5, "year": 2025, "headcount": 5},
    )

    token_resp = await client.post(
        f"/api/startups/{startup_id}/report-tokens",
        json={"month": 5, "year": 2025},
    )
    token = token_resp.json()["token"]

    ctx_resp = await client.get(f"/api/report/{token}")
    assert ctx_resp.json()["existing_indicator"]["headcount"] == 5

    resp = await client.post(
        f"/api/report/{token}/submit",
        json={"headcount": 12, "achievements": "Crescimento forte"},
    )
    assert resp.status_code == 204

    indicators_resp = await client.get(f"/api/startups/{startup_id}/indicators")
    items = indicators_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["headcount"] == 12


@pytest.mark.asyncio
async def test_invalid_token_returns_404(client):
    resp = await client.get("/api/report/00000000-0000-0000-0000-000000000001")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_generate_token_future_period_returns_400(client):
    startup_resp = await client.post(
        "/api/startups",
        json={"name": "Acme", "sector": "fintech", "investment_date": "2025-01-01"},
    )
    startup_id = startup_resp.json()["id"]

    resp = await client.post(
        f"/api/startups/{startup_id}/report-tokens",
        json={"month": 12, "year": 2099},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_generate_token_nonexistent_startup_returns_404(client):
    resp = await client.post(
        "/api/startups/00000000-0000-0000-0000-000000000001/report-tokens",
        json={"month": 1, "year": 2025},
    )
    assert resp.status_code == 404
