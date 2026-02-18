import pytest


@pytest.mark.asyncio
async def test_list_meetings_empty(client):
    startup_resp = await client.post(
        "/api/startups",
        json={
            "name": "Test Startup",
            "sector": "tech",
            "investment_date": "2026-01-15",
        },
    )
    startup_id = startup_resp.json()["id"]

    resp = await client.get(f"/api/startups/{startup_id}/meetings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_meeting(client):
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
        f"/api/startups/{startup_id}/meetings",
        json={
            "meeting_date": "2026-02-10",
            "participants": "Joao, Maria, Pedro",
            "summary": "Discussao sobre roadmap Q1",
            "attention_points": "Burn rate elevado",
            "next_steps": "Revisar projecoes financeiras",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["meeting_date"] == "2026-02-10"
    assert data["participants"] == "Joao, Maria, Pedro"
    assert data["summary"] == "Discussao sobre roadmap Q1"
    assert data["startup_id"] == startup_id
    assert "id" in data


@pytest.mark.asyncio
async def test_create_meeting_required_fields_only(client):
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
        f"/api/startups/{startup_id}/meetings",
        json={"meeting_date": "2026-03-01"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["meeting_date"] == "2026-03-01"
    assert data["participants"] is None


@pytest.mark.asyncio
async def test_get_meeting(client):
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
        f"/api/startups/{startup_id}/meetings",
        json={"meeting_date": "2026-02-15", "summary": "Reuniao mensal"},
    )
    meeting_id = create_resp.json()["id"]

    resp = await client.get(f"/api/startups/{startup_id}/meetings/{meeting_id}")
    assert resp.status_code == 200
    assert resp.json()["summary"] == "Reuniao mensal"


@pytest.mark.asyncio
async def test_update_meeting(client):
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
        f"/api/startups/{startup_id}/meetings",
        json={"meeting_date": "2026-02-20", "summary": "Original"},
    )
    meeting_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/startups/{startup_id}/meetings/{meeting_id}",
        json={"summary": "Atualizado", "attention_points": "Novo ponto"},
    )
    assert resp.status_code == 200
    assert resp.json()["summary"] == "Atualizado"
    assert resp.json()["attention_points"] == "Novo ponto"


@pytest.mark.asyncio
async def test_delete_meeting(client):
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
        f"/api/startups/{startup_id}/meetings",
        json={"meeting_date": "2026-02-25"},
    )
    meeting_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/startups/{startup_id}/meetings/{meeting_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/startups/{startup_id}/meetings/{meeting_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_meeting_startup_not_found(client):
    fake_id = "00000000-0000-0000-0000-000000000001"
    resp = await client.get(f"/api/startups/{fake_id}/meetings")
    assert resp.status_code == 404
