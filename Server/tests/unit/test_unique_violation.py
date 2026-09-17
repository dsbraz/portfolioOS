import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories.monthly_indicator_repository import _is_unique_violation


class _PostgresError(Exception):
    def __init__(self, sqlstate: str) -> None:
        super().__init__("violation")
        self.sqlstate = sqlstate


# The suite runs on SQLite, so the PostgreSQL branch is only reachable here.
@pytest.mark.parametrize(
    ("orig", "expected"),
    [
        (_PostgresError("23505"), True),
        (_PostgresError("23503"), False),
        (Exception("UNIQUE constraint failed: monthly_indicators.startup_id"), True),
        (Exception("FOREIGN KEY constraint failed"), False),
    ],
)
def test_only_a_duplicate_key_counts_as_a_conflict(orig: Exception, expected: bool):
    error = IntegrityError("INSERT ...", {}, orig)

    assert _is_unique_violation(error) is expected
