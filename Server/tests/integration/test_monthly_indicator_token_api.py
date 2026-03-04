from datetime import date

import pytest


def _token_reference_period() -> tuple[int, int]:
    """Mirror production rollover logic for expected token period."""
    today = date.today()
    months_back = 1 if today.day >= 10 else 2
    target_month = today.month - months_back
    target_year = today.year

    while target_month <= 0:
        target_month += 12
        target_year -= 1

    return target_month, target_year


@pytest.mark.asyncio
async def test_create_token(client, startup_id):
    expected_month, expected_year = _token_reference_period()

    resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["month"] == expected_month
    assert data["year"] == expected_year
    assert data["startup_id"] == startup_id
    assert "token" in data


@pytest.mark.asyncio
async def test_create_token_is_idempotent(client, startup_id):
    resp1 = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
    )
    resp2 = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
    )
    assert resp1.json()["token"] == resp2.json()["token"]


@pytest.mark.asyncio
async def test_list_tokens(client, startup_id):
    await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
    )

    resp = await client.get(f"/api/startups/{startup_id}/monthly-indicator-tokens")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_public_get_form_no_existing_indicator(client, startup_id):
    expected_month, expected_year = _token_reference_period()

    token_resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
    )
    token = token_resp.json()["token"]

    resp = await client.get(f"/api/monthly-indicator/{token}")
    assert resp.status_code == 200
    ctx = resp.json()
    assert ctx["startup_name"] == "Test Startup"
    assert ctx["month"] == expected_month
    assert ctx["year"] == expected_year
    assert ctx["existing_indicator"] is None


@pytest.mark.asyncio
async def test_public_submit_creates_indicator(client, startup_id):
    expected_month, expected_year = _token_reference_period()

    token_resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
    )
    token = token_resp.json()["token"]

    resp = await client.post(
        f"/api/monthly-indicator/{token}",
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

    indicators_resp = await client.get(f"/api/startups/{startup_id}/monthly-indicators")
    items = indicators_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["month"] == expected_month
    assert float(items[0]["total_revenue"]) == 100000.0


@pytest.mark.asyncio
async def test_public_submit_updates_existing_indicator(client, startup_id):
    expected_month, expected_year = _token_reference_period()

    await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": expected_month, "year": expected_year, "headcount": 5},
    )

    token_resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
    )
    token = token_resp.json()["token"]

    ctx_resp = await client.get(f"/api/monthly-indicator/{token}")
    assert ctx_resp.json()["existing_indicator"]["headcount"] == 5

    resp = await client.post(
        f"/api/monthly-indicator/{token}",
        json={"headcount": 12, "achievements": "Crescimento forte"},
    )
    assert resp.status_code == 204

    indicators_resp = await client.get(f"/api/startups/{startup_id}/monthly-indicators")
    items = indicators_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["headcount"] == 12


@pytest.mark.asyncio
async def test_public_invalid_token_returns_404(client):
    resp = await client.get("/api/monthly-indicator/00000000-0000-0000-0000-000000000001")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_token_nonexistent_startup_returns_404(client):
    resp = await client.post(
        "/api/startups/00000000-0000-0000-0000-000000000001/monthly-indicator-tokens",
    )
    assert resp.status_code == 404
