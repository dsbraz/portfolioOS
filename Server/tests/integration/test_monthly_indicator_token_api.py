import uuid
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken


def _current_period() -> tuple[int, int]:
    today = date.today()
    return today.month, today.year


def _future_period() -> tuple[int, int]:
    today = date.today()
    if today.month == 12:
        return 1, today.year + 1
    return today.month + 1, today.year


@pytest_asyncio.fixture
async def future_token(session: AsyncSession, startup_id: str) -> str:
    """Insert a token with a future period directly in the DB, bypassing use-case validation."""
    month, year = _future_period()
    token_value = uuid.uuid4()
    token = MonthlyIndicatorToken(
        startup_id=uuid.UUID(startup_id),
        token=token_value,
        month=month,
        year=year,
    )
    session.add(token)
    await session.flush()
    return str(token_value)


@pytest.mark.asyncio
async def test_create_token(client, startup_id):
    expected_month, expected_year = _current_period()

    resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
        json={"month": expected_month, "year": expected_year},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["month"] == expected_month
    assert data["year"] == expected_year
    assert data["startup_id"] == startup_id
    assert "token" in data


@pytest.mark.asyncio
async def test_create_token_is_idempotent(client, startup_id):
    month, year = _current_period()

    resp1 = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
        json={"month": month, "year": year},
    )
    resp2 = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
        json={"month": month, "year": year},
    )
    assert resp1.json()["token"] == resp2.json()["token"]


@pytest.mark.asyncio
async def test_list_tokens(client, startup_id):
    month, year = _current_period()

    await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
        json={"month": month, "year": year},
    )

    resp = await client.get(f"/api/startups/{startup_id}/monthly-indicator-tokens")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_public_get_form_no_existing_indicator(client, startup_id):
    expected_month, expected_year = _current_period()

    token_resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
        json={"month": expected_month, "year": expected_year},
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
    expected_month, expected_year = _current_period()

    token_resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
        json={"month": expected_month, "year": expected_year},
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
    expected_month, expected_year = _current_period()

    await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": expected_month, "year": expected_year, "headcount": 5},
    )

    token_resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
        json={"month": expected_month, "year": expected_year},
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
    resp = await client.get(
        "/api/monthly-indicator/00000000-0000-0000-0000-000000000001"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_token_nonexistent_startup_returns_404(client):
    month, year = _current_period()

    resp = await client.post(
        "/api/startups/00000000-0000-0000-0000-000000000001/monthly-indicator-tokens",
        json={"month": month, "year": year},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_token_without_body_returns_422(client, startup_id):
    resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_token_future_period_returns_400(client, startup_id):
    month, year = _future_period()

    resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
        json={"month": month, "year": year},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_public_submit_with_future_period_returns_400(
    client: AsyncClient, session: AsyncSession, future_token: str
):
    """Regression: public submit with a future-period token must return 400 with a structured
    detail message, not a 500 Internal Server Error."""
    resp = await client.post(
        f"/api/monthly-indicator/{future_token}",
        json={"headcount": 5},
    )
    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert data["detail"] != ""


@pytest.mark.asyncio
async def test_public_submit_negative_percentage_returns_422(client, startup_id):
    """Pydantic must reject negative values for percentage fields."""
    month, year = _current_period()

    token_resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
        json={"month": month, "year": year},
    )
    token = token_resp.json()["token"]

    resp = await client.post(
        f"/api/monthly-indicator/{token}",
        json={"recurring_revenue_pct": -1},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_public_submit_negative_headcount_returns_422(client, startup_id):
    """Pydantic must reject negative headcount."""
    month, year = _current_period()

    token_resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
        json={"month": month, "year": year},
    )
    token = token_resp.json()["token"]

    resp = await client.post(
        f"/api/monthly-indicator/{token}",
        json={"headcount": -1},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_public_submit_oversized_money_returns_422(client, startup_id):
    """Pydantic must reject values exceeding Numeric(15,2) capacity."""
    month, year = _current_period()

    token_resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
        json={"month": month, "year": year},
    )
    token = token_resp.json()["token"]

    resp = await client.post(
        f"/api/monthly-indicator/{token}",
        json={"total_revenue": 99_999_999_999_999_999},
    )
    assert resp.status_code == 422
