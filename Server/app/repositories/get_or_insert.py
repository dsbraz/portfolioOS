"""Insert-or-read-the-winner on a unique key, shared by the repositories.

Repositories absorb insert races on unique keys (CLAUDE.md, error handling), so
use cases keep only the business rule. Two requests that both miss the lookup
both try to insert; the loser's unique violation is caught inside a savepoint,
which keeps the session usable, and the row that won is read back.
"""

from collections.abc import Awaitable, Callable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import ConflictError


def is_unique_violation(error: IntegrityError) -> bool:
    """Only a duplicate is a conflict; a broken foreign key or NOT NULL is not.

    PostgreSQL reports SQLSTATE 23505; SQLite says so only in the message.
    """
    return (
        getattr(error.orig, "sqlstate", None) == "23505"
        or "UNIQUE constraint failed" in str(error.orig)
    )


async def insert_or_conflict[T](
    session: AsyncSession, record: T, conflict_message: str
) -> None:
    """Insert `record` in a savepoint; a duplicate becomes a `ConflictError`."""
    try:
        async with session.begin_nested():
            session.add(record)
            await session.flush()
    except IntegrityError as error:
        if not is_unique_violation(error):
            raise
        raise ConflictError(conflict_message) from error
    await session.refresh(record)


async def get_or_insert[T](
    session: AsyncSession,
    record: T,
    find: Callable[[], Awaitable[T | None]],
    conflict_message: str,
) -> tuple[T, bool]:
    """The stored row `find` returns, or `record` inserted; and whether it was."""
    existing = await find()
    if existing is not None:
        return existing, False
    try:
        await insert_or_conflict(session, record, conflict_message)
    except ConflictError:
        # Another request took the key after the lookup; read the row that won.
        winner = await find()
        if winner is None:
            raise
        return winner, False
    return record, True
