import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.executive.create_executive import CreateExecutive
from app.application.executive.update_executive import UpdateExecutive
from app.domain.exceptions import InvalidInputError
from app.domain.models.executive import Executive


def _executive(**values):
    return Executive(startup_id=uuid.uuid4(), name="Ana", **values)


@pytest.mark.asyncio
@pytest.mark.parametrize("email", [None, "", "   "])
async def test_create_refuses_a_marked_executive_without_email(email):
    repo = AsyncMock()

    with pytest.raises(InvalidInputError, match="e-mail"):
        await CreateExecutive(repo).execute(
            _executive(email=email, receives_monthly_report=True)
        )
    repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_checks_the_merged_record_before_touching_it():
    repo = AsyncMock()
    executive = _executive(email="ana@x.com", receives_monthly_report=True)

    with pytest.raises(InvalidInputError):
        await UpdateExecutive(repo).execute(executive, {"email": None})

    assert executive.email == "ana@x.com"
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_allows_unmarking_and_clearing_together():
    repo = AsyncMock()
    repo.update.side_effect = lambda e: e
    executive = _executive(email="ana@x.com", receives_monthly_report=True)

    await UpdateExecutive(repo).execute(
        executive, {"email": None, "receives_monthly_report": False}
    )

    assert executive.email is None and executive.receives_monthly_report is False
