"""The reporting e-mail is pinned to the cases file the client reads too.

The initial e-mail exists in the panel (manual send) and in the monthly job;
both read these cases, so they cannot drift. The file lives with the client and
is mounted read-only here by both compose files.
"""

import json
from pathlib import Path

import pytest

from app.domain.models.monthly_report_dispatch import DispatchKind
from app.domain.reporting_message import build_reporting_email

_CASES = Path("/contracts/reporting-message.cases.json")
if not _CASES.is_file():
    _CASES = (
        Path(__file__).resolve().parents[3]
        / "Client"
        / "src"
        / "app"
        / "models"
        / "reporting-message.cases.json"
    )
CASES = json.loads(_CASES.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["name"])
def test_message_matches_the_shared_cases(case):
    data = case["input"]

    message = build_reporting_email(
        DispatchKind(case["kind"]),
        executive_name=data["executiveName"],
        startup_name=data["startupName"],
        month=data["month"],
        year=data["year"],
        form_url=data["formUrl"],
    )

    assert message.subject == case["subject"]
    assert message.body == case["body"]


def test_both_kinds_are_pinned():
    assert {c["kind"] for c in CASES} == {k.value for k in DispatchKind}


def test_signature_closes_the_message_when_configured():
    data = CASES[0]["input"]

    message = build_reporting_email(
        DispatchKind.INITIAL,
        data["executiveName"],
        data["startupName"],
        data["month"],
        data["year"],
        data["formUrl"],
        signature="  Equipe de Portfólio  ",
    )

    assert message.body == CASES[0]["body"] + "\nEquipe de Portfólio"


def test_blank_signature_adds_nothing():
    data = CASES[0]["input"]

    message = build_reporting_email(
        DispatchKind.INITIAL,
        data["executiveName"],
        data["startupName"],
        data["month"],
        data["year"],
        data["formUrl"],
        signature=" ",
    )

    assert message.body == CASES[0]["body"]
