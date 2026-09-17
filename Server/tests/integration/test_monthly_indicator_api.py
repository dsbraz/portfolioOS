import pytest

from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository


@pytest.mark.asyncio
async def test_list_indicators_empty(client, startup_id):
    resp = await client.get(f"/api/startups/{startup_id}/monthly-indicators")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_indicator(client, startup_id):
    resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
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
async def test_create_indicator_required_fields_only(client, startup_id):
    resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 1, "year": 2026},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["month"] == 1
    assert data["year"] == 2026
    assert data["total_revenue"] is None


@pytest.mark.asyncio
async def test_create_indicator_upsert(client, startup_id):
    resp1 = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 2, "year": 2026, "headcount": 5},
    )
    assert resp1.status_code == 201

    resp2 = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 2, "year": 2026, "headcount": 10},
    )
    assert resp2.status_code == 201
    assert resp2.json()["headcount"] == 10

    list_resp = await client.get(f"/api/startups/{startup_id}/monthly-indicators")
    assert list_resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_get_indicator(client, startup_id):
    create_resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 1, "year": 2025, "headcount": 10},
    )
    indicator_id = create_resp.json()["id"]

    resp = await client.get(
        f"/api/startups/{startup_id}/monthly-indicators/{indicator_id}"
    )
    assert resp.status_code == 200
    assert resp.json()["headcount"] == 10


@pytest.mark.asyncio
async def test_update_indicator(client, startup_id):
    create_resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 1, "year": 2025, "headcount": 10},
    )
    indicator_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/startups/{startup_id}/monthly-indicators/{indicator_id}",
        json={"headcount": 15, "achievements": "Novo produto lancado"},
    )
    assert resp.status_code == 200
    assert resp.json()["headcount"] == 15
    assert resp.json()["achievements"] == "Novo produto lancado"


@pytest.mark.asyncio
async def test_delete_indicator(client, startup_id):
    create_resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 1, "year": 2025},
    )
    indicator_id = create_resp.json()["id"]

    resp = await client.delete(
        f"/api/startups/{startup_id}/monthly-indicators/{indicator_id}"
    )
    assert resp.status_code == 204

    resp = await client.get(
        f"/api/startups/{startup_id}/monthly-indicators/{indicator_id}"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_indicator_startup_not_found(client):
    fake_id = "00000000-0000-0000-0000-000000000001"
    resp = await client.get(f"/api/startups/{fake_id}/monthly-indicators")
    assert resp.status_code == 404


# --- Public reporting zone: contract guards (RFC-001 §3.4) -------------------


async def _token_for(client, startup_id: str, month: int, year: int) -> str:
    resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicator-tokens",
        json={"month": month, "year": year},
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["token"]


@pytest.mark.asyncio
async def test_public_form_never_serializes_the_fund_note(
    client, anon_client, startup_id
):
    created = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={
            "month": 3,
            "year": 2026,
            "total_revenue": 1000,
            "comments": "Anotacao interna do fundo",
        },
    )
    assert created.status_code == 201

    token = await _token_for(client, startup_id, 3, 2026)
    resp = await anon_client.get(f"/api/monthly-indicator/{token}")

    assert resp.status_code == 200
    existing = resp.json()["existing_indicator"]
    assert existing is not None
    # The note exists on the record; the public payload must not reveal it.
    assert "comments" not in existing
    assert "Anotacao interna do fundo" not in resp.text


@pytest.mark.asyncio
async def test_public_resubmit_preserves_the_fund_note(client, anon_client, startup_id):
    await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={
            "month": 4,
            "year": 2026,
            "total_revenue": 1000,
            "comments": "Anotacao que precisa sobreviver",
        },
    )
    token = await _token_for(client, startup_id, 4, 2026)

    submitted = await anon_client.post(
        f"/api/monthly-indicator/{token}",
        json={"total_revenue": 2000, "headcount": 10},
    )
    assert submitted.status_code == 204

    listed = await client.get(f"/api/startups/{startup_id}/monthly-indicators")
    indicator = next(
        item
        for item in listed.json()["items"]
        if item["month"] == 4 and item["year"] == 2026
    )
    assert float(indicator["total_revenue"]) == 2000
    assert indicator["headcount"] == 10
    # The investee's re-submit carries no `comments`; it must not erase the note.
    assert indicator["comments"] == "Anotacao que precisa sobreviver"


@pytest.mark.asyncio
async def test_public_submit_rejects_a_value_outside_the_admin_limits(
    client, anon_client, startup_id
):
    token = await _token_for(client, startup_id, 5, 2026)

    resp = await anon_client.post(
        f"/api/monthly-indicator/{token}",
        json={"total_revenue": -999_000_000_000_000},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_patch_onto_an_occupied_period_conflicts_instead_of_crashing(
    client, startup_id
):
    first = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 6, "year": 2026, "total_revenue": 100},
    )
    second = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 7, "year": 2026, "total_revenue": 200},
    )
    assert first.status_code == 201 and second.status_code == 201

    # The edit dialog sends the period on every save, so this is reachable in
    # normal use; startup plus period is unique.
    resp = await client.patch(
        f"/api/startups/{startup_id}/monthly-indicators/{second.json()['id']}",
        json={"month": 6, "year": 2026},
    )

    assert resp.status_code == 409
    assert "6/2026" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_patch_that_loses_a_race_for_the_period_still_conflicts(
    client, startup_id, monkeypatch
):
    first = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 8, "year": 2026},
    )
    second = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 9, "year": 2026},
    )
    assert first.status_code == 201 and second.status_code == 201

    # Another request takes the period between the check and the write: the
    # check sees it free, so only the unique constraint can catch it.
    async def period_looks_free(*_args, **_kwargs):
        return None

    monkeypatch.setattr(
        MonthlyIndicatorRepository, "get_by_startup_and_period", period_looks_free
    )

    resp = await client.patch(
        f"/api/startups/{startup_id}/monthly-indicators/{second.json()['id']}",
        json={"month": 8, "year": 2026},
    )

    assert resp.status_code == 409
    # The handler answers after the session rolled back: the move did not stick.
    stored = await client.get(
        f"/api/startups/{startup_id}/monthly-indicators/{second.json()['id']}"
    )
    assert stored.json()["month"] == 9


@pytest.mark.asyncio
async def test_create_that_loses_a_race_for_the_period_merges_into_the_winner(
    client, startup_id, monkeypatch
):
    winner = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 10, "year": 2025, "total_revenue": 100},
    )
    assert winner.status_code == 201

    # The second create checks while the period still looks free, then inserts
    # after the first one committed. Creating is an upsert, so it must merge.
    real_lookup = MonthlyIndicatorRepository.get_by_startup_and_period
    calls = 0

    async def free_on_first_look(self, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return None
        return await real_lookup(self, *args, **kwargs)

    monkeypatch.setattr(
        MonthlyIndicatorRepository, "get_by_startup_and_period", free_on_first_look
    )

    loser = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 10, "year": 2025, "headcount": 7},
    )

    assert loser.status_code == 201
    assert loser.json()["id"] == winner.json()["id"]
    assert loser.json()["headcount"] == 7
    assert float(loser.json()["total_revenue"]) == 100


@pytest.mark.asyncio
async def test_create_that_conflicts_with_no_visible_winner_answers_409(
    client, startup_id, monkeypatch
):
    first = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 11, "year": 2025},
    )
    assert first.status_code == 201

    # The insert conflicts but the winner is not visible yet: no merge target.
    async def period_looks_free(*_args, **_kwargs):
        return None

    monkeypatch.setattr(
        MonthlyIndicatorRepository, "get_by_startup_and_period", period_looks_free
    )

    resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 11, "year": 2025, "headcount": 7},
    )

    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_patch_rejects_a_null_period(client, startup_id):
    created = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 3, "year": 2025},
    )

    resp = await client.patch(
        f"/api/startups/{startup_id}/monthly-indicators/{created.json()['id']}",
        json={"month": None},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_patch_keeping_its_own_period_is_not_a_conflict(client, startup_id):
    created = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 8, "year": 2026, "total_revenue": 100},
    )

    resp = await client.patch(
        f"/api/startups/{startup_id}/monthly-indicators/{created.json()['id']}",
        json={"month": 8, "year": 2026, "total_revenue": 300},
    )

    assert resp.status_code == 200
    assert float(resp.json()["total_revenue"]) == 300


@pytest.mark.asyncio
async def test_headcount_above_the_column_capacity_is_refused_not_crashed(
    client, startup_id
):
    resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": 9, "year": 2026, "headcount": 2_147_483_648},
    )

    assert resp.status_code == 422
