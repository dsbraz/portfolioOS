import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.monthly_report.plan_monthly_report import PlanMonthlyReport
from app.application.monthly_report.send_monthly_report import SendMonthlyReport
from app.domain.models.monthly_report_dispatch import DispatchKind
from app.domain.models.period import Period
from app.repositories.executive_repository import ExecutiveRepository
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository
from app.repositories.monthly_report_dispatch_repository import (
    MonthlyReportDispatchRepository,
)
from app.repositories.startup_repository import StartupRepository


class _Outbox:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))


def _closed_period() -> Period:
    today = date.today()
    return Period(year=today.year, month=today.month).previous()


async def _run(session: AsyncSession, startup_id: str, kind: DispatchKind, outbox):
    """The job's two steps, against the real repositories and unique keys."""
    startup = await StartupRepository(session).get_by_id(uuid.UUID(startup_id))
    plan = await PlanMonthlyReport(
        ExecutiveRepository(session), MonthlyIndicatorRepository(session)
    ).execute(startup, kind)
    if plan is None:
        return []
    send = SendMonthlyReport(
        MonthlyReportDispatchRepository(session),
        outbox,
        "https://portfolio.example.com",
    )
    sent = [await send.execute(plan, r) for r in plan.recipients]
    return [d for d in sent if d is not None]


async def _opt_in(client: AsyncClient, startup_id: str) -> None:
    resp = await client.patch(
        f"/api/startups/{startup_id}", json={"monthly_report_enabled": True}
    )
    assert resp.status_code == 200
    resp = await client.post(
        f"/api/startups/{startup_id}/executives",
        json={
            "name": "Ana Souza",
            "email": "ana@payface.com",
            "receives_monthly_report": True,
        },
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_new_flags_default_to_off_and_round_trip(client, startup_id):
    startup = (await client.get(f"/api/startups/{startup_id}")).json()
    assert startup["monthly_report_enabled"] is False

    await _opt_in(client, startup_id)

    startup = (await client.get(f"/api/startups/{startup_id}")).json()
    assert startup["monthly_report_enabled"] is True
    executives = (await client.get(f"/api/startups/{startup_id}/executives")).json()
    assert executives["items"][0]["receives_monthly_report"] is True


@pytest.mark.asyncio
async def test_only_opted_in_startups_are_listed_for_the_job(
    client, session, startup_id
):
    other = await client.post(
        "/api/startups",
        json={"name": "Off", "sector": "tech", "investment_date": "2026-01-15"},
    )
    await _opt_in(client, startup_id)

    startups = await StartupRepository(session).get_all_with_monthly_report_enabled()

    ids = {str(s.id) for s in startups}
    assert startup_id in ids
    assert other.json()["id"] not in ids


@pytest.mark.asyncio
async def test_dispatch_sends_once_and_is_listed(client, session, startup_id):
    await _opt_in(client, startup_id)
    outbox = _Outbox()

    first = await _run(session, startup_id, DispatchKind.INITIAL, outbox)
    second = await _run(session, startup_id, DispatchKind.INITIAL, outbox)

    assert len(first) == 1 and second == []
    assert len(outbox.sent) == 1
    period = _closed_period()
    # The link e-mailed is the one the panel lists for the period.
    tokens = (
        await client.get(f"/api/startups/{startup_id}/monthly-indicator-tokens")
    ).json()["items"]
    assert [(t["month"], t["year"]) for t in tokens] == [(period.month, period.year)]
    assert tokens[0]["token"] in outbox.sent[0][2]

    resp = await client.get(f"/api/startups/{startup_id}/monthly-report-dispatches")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["recipient_email"] == "ana@payface.com"
    assert (item["month"], item["year"], item["kind"]) == (
        period.month,
        period.year,
        "initial",
    )
    assert item["error"] is None


@pytest.mark.asyncio
async def test_reminder_is_not_sent_once_the_period_is_reported(
    client, session, startup_id
):
    await _opt_in(client, startup_id)
    period = _closed_period()
    resp = await client.post(
        f"/api/startups/{startup_id}/monthly-indicators",
        json={"month": period.month, "year": period.year},
    )
    assert resp.status_code == 201, resp.text
    outbox = _Outbox()

    sent = await _run(session, startup_id, DispatchKind.REMINDER, outbox)

    assert sent == [] and outbox.sent == []


@pytest.mark.asyncio
async def test_reminder_after_the_initial_sends_the_reminder_once(
    client, session, startup_id
):
    await _opt_in(client, startup_id)
    outbox = _Outbox()
    await _run(session, startup_id, DispatchKind.INITIAL, outbox)

    first = await _run(session, startup_id, DispatchKind.REMINDER, outbox)
    again = await _run(session, startup_id, DispatchKind.REMINDER, outbox)

    assert [d.kind for d in first] == [DispatchKind.REMINDER] and again == []
    assert outbox.sent[1][1].startswith("Lembrete:")


@pytest.mark.asyncio
async def test_reminder_without_an_initial_sends_the_initial_instead(
    client, session, startup_id
):
    await _opt_in(client, startup_id)
    outbox = _Outbox()

    sent = await _run(session, startup_id, DispatchKind.REMINDER, outbox)

    assert [d.kind for d in sent] == [DispatchKind.INITIAL]
    assert not outbox.sent[0][1].startswith("Lembrete:")


@pytest.mark.asyncio
async def test_dispatches_of_unknown_startup_is_404(client):
    resp = await client.get(f"/api/startups/{uuid.uuid4()}/monthly-report-dispatches")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_marking_an_executive_without_email_is_refused(client, startup_id):
    resp = await client.post(
        f"/api/startups/{startup_id}/executives",
        json={"name": "Sem E-mail", "receives_monthly_report": True},
    )

    assert resp.status_code == 400
    assert "e-mail" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_clearing_the_email_of_a_marked_executive_is_refused(client, startup_id):
    await _opt_in(client, startup_id)
    executive = (await client.get(f"/api/startups/{startup_id}/executives")).json()[
        "items"
    ][0]

    resp = await client.patch(
        f"/api/startups/{startup_id}/executives/{executive['id']}",
        json={"email": None},
    )
    assert resp.status_code == 400

    # Unmarking and clearing together is a coherent change.
    resp = await client.patch(
        f"/api/startups/{startup_id}/executives/{executive['id']}",
        json={"email": None, "receives_monthly_report": False},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_explicit_null_flags_are_a_validation_error_not_a_500(
    client, startup_id
):
    resp = await client.patch(
        f"/api/startups/{startup_id}", json={"monthly_report_enabled": None}
    )
    assert resp.status_code == 422

    created = await client.post(
        f"/api/startups/{startup_id}/executives", json={"name": "Ana"}
    )
    resp = await client.patch(
        f"/api/startups/{startup_id}/executives/{created.json()['id']}",
        json={"receives_monthly_report": None},
    )
    assert resp.status_code == 422
