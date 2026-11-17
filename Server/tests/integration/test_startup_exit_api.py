"""Recording a startup's exit and what "stop tracking it" means across the API."""

from datetime import date, timedelta

import pytest
from httpx import AsyncClient


EXIT = {"exited_on": "2026-03-20", "exit_type": "venda", "exit_notes": "Big Co"}


async def _create_startup(client: AsyncClient, name: str) -> str:
    resp = await client.post(
        "/api/startups",
        json={"name": name, "sector": "tech", "investment_date": "2025-01-10"},
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_record_exit(client: AsyncClient, startup_id: str):
    resp = await client.put(f"/api/startups/{startup_id}/exit", json=EXIT)

    assert resp.status_code == 200
    data = resp.json()
    assert data["exited_on"] == "2026-03-20"
    assert data["exit_type"] == "venda"
    assert data["exit_notes"] == "Big Co"

    fetched = (await client.get(f"/api/startups/{startup_id}")).json()
    assert fetched["exited_on"] == "2026-03-20"


@pytest.mark.asyncio
async def test_a_new_startup_has_no_exit(client: AsyncClient, startup_id: str):
    data = (await client.get(f"/api/startups/{startup_id}")).json()

    assert data["exited_on"] is None
    assert data["exit_type"] is None
    assert data["exit_notes"] is None


@pytest.mark.asyncio
async def test_record_exit_twice_is_409(client: AsyncClient, startup_id: str):
    await client.put(f"/api/startups/{startup_id}/exit", json=EXIT)

    resp = await client.put(f"/api/startups/{startup_id}/exit", json=EXIT)

    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_record_exit_in_the_future_is_400(client: AsyncClient, startup_id: str):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    resp = await client.put(
        f"/api/startups/{startup_id}/exit",
        json={"exited_on": tomorrow, "exit_type": "baixa"},
    )

    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_record_exit_before_the_investment_is_400(
    client: AsyncClient, startup_id: str
):
    # The `startup_id` fixture invests on 2026-01-15.
    resp = await client.put(
        f"/api/startups/{startup_id}/exit",
        json={"exited_on": "2026-01-14", "exit_type": "baixa"},
    )

    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_record_exit_with_unknown_type_is_422(client: AsyncClient, startup_id: str):
    resp = await client.put(
        f"/api/startups/{startup_id}/exit",
        json={"exited_on": "2026-03-20", "exit_type": "fusao"},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_record_exit_on_missing_startup_is_404(client: AsyncClient):
    resp = await client.put(
        "/api/startups/00000000-0000-0000-0000-000000000001/exit", json=EXIT
    )

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_undo_exit(client: AsyncClient, startup_id: str):
    await client.put(f"/api/startups/{startup_id}/exit", json=EXIT)

    resp = await client.delete(f"/api/startups/{startup_id}/exit")

    assert resp.status_code == 200
    assert resp.json()["exited_on"] is None
    assert resp.json()["exit_type"] is None


@pytest.mark.asyncio
async def test_undo_without_exit_is_409(client: AsyncClient, startup_id: str):
    resp = await client.delete(f"/api/startups/{startup_id}/exit")

    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_undo_on_missing_startup_is_404(client: AsyncClient):
    resp = await client.delete(
        "/api/startups/00000000-0000-0000-0000-000000000001/exit"
    )

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_filters_by_tracked(client: AsyncClient):
    tracked_id = await _create_startup(client, "Ativa")
    exited_id = await _create_startup(client, "Vendida")
    await client.put(f"/api/startups/{exited_id}/exit", json=EXIT)

    all_items = (await client.get("/api/startups")).json()
    tracked = (await client.get("/api/startups?tracked=true")).json()
    exited = (await client.get("/api/startups?tracked=false")).json()

    assert all_items["total"] == 2
    assert [s["id"] for s in tracked["items"]] == [tracked_id]
    assert tracked["total"] == 1
    assert [s["id"] for s in exited["items"]] == [exited_id]
    assert exited["total"] == 1


async def _summary(client: AsyncClient, month: int) -> dict:
    return (await client.get(f"/api/portfolio/summary?month={month}&year=2026")).json()


@pytest.mark.asyncio
async def test_portfolio_counts_before_the_exit_and_stops_after_it(client: AsyncClient):
    await _create_startup(client, "Ativa")
    exited_id = await _create_startup(client, "Vendida")
    await client.put(f"/api/startups/{exited_id}/exit", json=EXIT)

    before_exit = await _summary(client, 2)
    after_exit = await _summary(client, 4)

    assert before_exit["total_startups"] == 2
    assert after_exit["total_startups"] == 1
    assert [row["startup"]["name"] for row in after_exit["startups"]] == ["Ativa"]


@pytest.mark.asyncio
async def test_unreported_exit_month_is_not_a_pending_report(client: AsyncClient):
    # The links are closed by the exit, so the month could never be reported.
    await _create_startup(client, "Ativa")
    exited_id = await _create_startup(client, "Vendida")
    await client.put(f"/api/startups/{exited_id}/exit", json=EXIT)

    in_exit_month = await _summary(client, 3)

    assert in_exit_month["total_startups"] == 1
    assert [row["startup"]["name"] for row in in_exit_month["startups"]] == ["Ativa"]


@pytest.mark.asyncio
async def test_reported_exit_month_keeps_its_numbers(client: AsyncClient):
    await _create_startup(client, "Ativa")
    exited_id = await _create_startup(client, "Vendida")
    await client.post(
        f"/api/startups/{exited_id}/monthly-indicators",
        json={"month": 3, "year": 2026, "total_revenue": 5000},
    )
    await client.put(f"/api/startups/{exited_id}/exit", json=EXIT)

    in_exit_month = await _summary(client, 3)

    assert in_exit_month["total_startups"] == 2
    assert float(in_exit_month["revenue"]) == 5000
    assert in_exit_month["monthly_report_pct"] == 50.0


@pytest.mark.asyncio
async def test_investment_date_after_the_exit_is_400(client: AsyncClient, startup_id: str):
    await client.put(f"/api/startups/{startup_id}/exit", json=EXIT)

    resp = await client.patch(
        f"/api/startups/{startup_id}", json={"investment_date": "2026-04-01"}
    )

    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_exit_month_numbers_can_still_be_entered_by_hand(client: AsyncClient):
    # The numbers often arrive after the exit is recorded.
    await _create_startup(client, "Ativa")
    exited_id = await _create_startup(client, "Vendida")
    await client.put(f"/api/startups/{exited_id}/exit", json=EXIT)

    resp = await client.post(
        f"/api/startups/{exited_id}/monthly-indicators",
        json={"month": 3, "year": 2026, "total_revenue": 5000},
    )

    assert resp.status_code == 201
    assert (await _summary(client, 3))["total_startups"] == 2


@pytest.mark.asyncio
async def test_no_indicator_after_the_exit_month_is_accepted(
    client: AsyncClient, startup_id: str
):
    await client.put(f"/api/startups/{startup_id}/exit", json=EXIT)

    resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 4, "year": 2026, "total_revenue": 5000},
    )

    assert resp.status_code == 409
    indicators = (
        await client.get(f"/api/startups/{startup_id}/monthly-indicators")
    ).json()
    assert indicators["total"] == 0


@pytest.mark.asyncio
async def test_exit_before_a_reported_month_is_400(client: AsyncClient, startup_id: str):
    await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 5, "year": 2026, "total_revenue": 5000},
    )

    resp = await client.put(f"/api/startups/{startup_id}/exit", json=EXIT)

    assert resp.status_code == 400
    assert "05/2026" in resp.json()["detail"]
    fetched = (await client.get(f"/api/startups/{startup_id}")).json()
    assert fetched["exited_on"] is None


@pytest.mark.asyncio
async def test_portfolio_with_only_exited_startups_is_empty(client: AsyncClient):
    exited_id = await _create_startup(client, "Vendida")
    await client.put(f"/api/startups/{exited_id}/exit", json=EXIT)

    data = (await client.get("/api/portfolio/summary?month=4&year=2026")).json()

    assert data["total_startups"] == 0
    assert data["startups"] == []


async def _token(client: AsyncClient, startup_id: str, month: int, year: int) -> str:
    resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
        json={"month": month, "year": year},
    )
    return resp.json()["token"]


@pytest.mark.asyncio
@pytest.mark.parametrize("month", [2, 3, 4], ids=["before", "exit-month", "after"])
async def test_every_public_link_of_an_exited_startup_is_refused(
    client: AsyncClient, anon_client: AsyncClient, startup_id: str, month: int
):
    # An exited startup has no reporting link at all, whatever its period.
    token = await _token(client, startup_id, month, 2026)
    await client.put(f"/api/startups/{startup_id}/exit", json=EXIT)

    get_resp = await anon_client.get(f"/api/monthly-indicator/{token}")
    post_resp = await anon_client.post(
        f"/api/monthly-indicator/{token}", json={"total_revenue": 1000}
    )

    assert get_resp.status_code == 409
    assert post_resp.status_code == 409
    indicators = (
        await client.get(f"/api/startups/{startup_id}/monthly-indicators")
    ).json()
    assert indicators["total"] == 0


@pytest.mark.asyncio
async def test_an_exited_startup_cannot_get_a_new_link(
    client: AsyncClient, startup_id: str
):
    await client.put(f"/api/startups/{startup_id}/exit", json=EXIT)

    resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
        json={"month": 3, "year": 2026},
    )

    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_undoing_the_exit_brings_the_links_back(
    client: AsyncClient, anon_client: AsyncClient, startup_id: str
):
    token = await _token(client, startup_id, 3, 2026)
    await client.put(f"/api/startups/{startup_id}/exit", json=EXIT)
    await client.delete(f"/api/startups/{startup_id}/exit")

    resp = await anon_client.get(f"/api/monthly-indicator/{token}")

    assert resp.status_code == 200
