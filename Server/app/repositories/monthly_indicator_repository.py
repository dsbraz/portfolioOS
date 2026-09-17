import uuid
from collections.abc import Awaitable, Callable
from decimal import Decimal

from sqlalchemy import ColumnElement, Integer, cast, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import ConflictError
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken
from app.domain.models.period import Period


def _is_unique_violation(error: IntegrityError) -> bool:
    """Only a duplicate is a conflict; a broken foreign key or NOT NULL is not.

    PostgreSQL reports SQLSTATE 23505; SQLite says so only in the message.
    """
    return (
        getattr(error.orig, "sqlstate", None) == "23505"
        or "UNIQUE constraint failed" in str(error.orig)
    )


def year_month_key_expression() -> ColumnElement[int]:
    """`year * 100 + month` as a comparable, sortable integer (202607).

    SQL counterpart of `Period.key`; results are decoded with `Period.from_key`.

    Avoids comparing two fields and the classic bug of Dec/2025 beating
    Jan/2026 for having a larger month.

    BOTH casts are required, not decorative: `year` and `month` are
    SMALLINT, and the sum's type follows the last operand. Casting only `year`,
    the comparison literal still went out as int16 -- 202607 overflows the 32767
    limit and asyncpg rejects the parameter at runtime.
    """
    return cast(MonthlyIndicator.year, Integer) * 100 + cast(
        MonthlyIndicator.month, Integer
    )


class MonthlyIndicatorRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_all_by_startup(
        self, startup_id: uuid.UUID
    ) -> tuple[list[MonthlyIndicator], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(MonthlyIndicator)
            .where(MonthlyIndicator.startup_id == startup_id)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(MonthlyIndicator)
            .where(MonthlyIndicator.startup_id == startup_id)
            .order_by(MonthlyIndicator.year.desc(), MonthlyIndicator.month.desc())
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, indicator_id: uuid.UUID) -> MonthlyIndicator | None:
        result = await self._session.execute(
            select(MonthlyIndicator).where(MonthlyIndicator.id == indicator_id)
        )
        return result.scalar_one_or_none()

    async def get_by_startup_and_period(
        self, startup_id: uuid.UUID, month: int, year: int
    ) -> MonthlyIndicator | None:
        result = await self._session.execute(
            select(MonthlyIndicator).where(
                MonthlyIndicator.startup_id == startup_id,
                MonthlyIndicator.month == month,
                MonthlyIndicator.year == year,
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self, indicator: MonthlyIndicator
    ) -> tuple[MonthlyIndicator, bool]:
        """The stored indicator for the period, or `indicator` inserted; and whether it was."""
        return await self._get_or_insert(
            indicator,
            lambda: self.get_by_startup_and_period(
                indicator.startup_id, indicator.month, indicator.year
            ),
            f"Ja existe indicador para o periodo {indicator.month}/{indicator.year}",
        )

    async def update(self, indicator: MonthlyIndicator) -> MonthlyIndicator:
        # Read before flushing: a failed flush invalidates the session and the
        # instance can no longer load its attributes.
        period = f"{indicator.month}/{indicator.year}"
        try:
            await self._session.flush()
        except IntegrityError as error:
            # The use case checks the period first; this catches the request that
            # took it in between. Startup plus period is the only unique key.
            if not _is_unique_violation(error):
                raise
            raise ConflictError(f"Ja existe indicador para o periodo {period}") from error
        await self._session.refresh(indicator)
        return indicator

    async def delete(self, indicator: MonthlyIndicator) -> None:
        await self._session.delete(indicator)
        await self._session.flush()

    async def get_by_startups_and_period(
        self, startup_ids: list[uuid.UUID], month: int, year: int
    ) -> dict[uuid.UUID, MonthlyIndicator]:
        if not startup_ids:
            return {}

        result = await self._session.execute(
            select(MonthlyIndicator).where(
                MonthlyIndicator.startup_id.in_(startup_ids),
                MonthlyIndicator.month == month,
                MonthlyIndicator.year == year,
            )
        )
        indicators = list(result.scalars().all())

        return {ind.startup_id: ind for ind in indicators}

    async def get_last_reported_period_by_startups(
        self, startup_ids: list[uuid.UUID], month: int, year: int
    ) -> dict[uuid.UUID, Period]:
        """Latest period reported per startup, UP TO the queried period.

        The upper bound matters: looking at Feb/2026, a Jul/2026 report is in
        the future relative to the screen's window, and showing it would say the
        startup reported something that, in that context, has not happened yet.

        Startups without any report are left out of the dict.
        """
        if not startup_ids:
            return {}

        period = year_month_key_expression()

        result = await self._session.execute(
            select(MonthlyIndicator.startup_id, func.max(period))
            .where(
                MonthlyIndicator.startup_id.in_(startup_ids),
                period <= Period(year=year, month=month).key,
            )
            .group_by(MonthlyIndicator.startup_id)
        )

        return {row[0]: Period.from_key(row[1]) for row in result.all()}

    async def get_accumulated_revenue_by_startups(
        self, startup_ids: list[uuid.UUID], month: int, year: int
    ) -> dict[uuid.UUID, Decimal]:
        if not startup_ids:
            return {}

        result = await self._session.execute(
            select(
                MonthlyIndicator.startup_id,
                func.sum(MonthlyIndicator.total_revenue),
            )
            .where(
                MonthlyIndicator.startup_id.in_(startup_ids),
                MonthlyIndicator.year == year,
                MonthlyIndicator.month <= month,
            )
            .group_by(MonthlyIndicator.startup_id)
        )

        return {row[0]: row[1] for row in result.all() if row[1] is not None}

    # --- Token methods ---

    async def get_token_by_value(
        self, token: uuid.UUID
    ) -> MonthlyIndicatorToken | None:
        result = await self._session.execute(
            select(MonthlyIndicatorToken).where(MonthlyIndicatorToken.token == token)
        )
        return result.scalar_one_or_none()

    async def get_token_by_startup_and_period(
        self, startup_id: uuid.UUID, month: int, year: int
    ) -> MonthlyIndicatorToken | None:
        result = await self._session.execute(
            select(MonthlyIndicatorToken).where(
                MonthlyIndicatorToken.startup_id == startup_id,
                MonthlyIndicatorToken.month == month,
                MonthlyIndicatorToken.year == year,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_tokens_by_startup(
        self, startup_id: uuid.UUID
    ) -> tuple[list[MonthlyIndicatorToken], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(MonthlyIndicatorToken)
            .where(MonthlyIndicatorToken.startup_id == startup_id)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(MonthlyIndicatorToken)
            .where(MonthlyIndicatorToken.startup_id == startup_id)
            .order_by(
                MonthlyIndicatorToken.year.desc(),
                MonthlyIndicatorToken.month.desc(),
            )
        )
        return list(result.scalars().all()), total

    async def get_or_create_token(
        self, token: MonthlyIndicatorToken
    ) -> tuple[MonthlyIndicatorToken, bool]:
        """The stored link for the period, or `token` inserted; and whether it was."""
        return await self._get_or_insert(
            token,
            lambda: self.get_token_by_startup_and_period(
                token.startup_id, token.month, token.year
            ),
            f"Ja existe link para o periodo {token.month}/{token.year}",
        )

    async def _get_or_insert[T: (MonthlyIndicator, MonthlyIndicatorToken)](
        self, record: T, find: Callable[[], Awaitable[T | None]], conflict_message: str
    ) -> tuple[T, bool]:
        existing = await find()
        if existing is not None:
            return existing, False
        try:
            await self._insert(record, conflict_message)
        except ConflictError:
            # Another request took the period after the lookup; the savepoint kept
            # the session usable, so read the row that won.
            winner = await find()
            if winner is None:
                raise
            return winner, False
        return record, True

    async def _insert(
        self, record: MonthlyIndicator | MonthlyIndicatorToken, conflict_message: str
    ) -> None:
        try:
            # A savepoint keeps the session usable when another request took the
            # period first, so the caller can still read the record that won.
            async with self._session.begin_nested():
                self._session.add(record)
                await self._session.flush()
        except IntegrityError as error:
            if not _is_unique_violation(error):
                raise
            raise ConflictError(conflict_message) from error
        await self._session.refresh(record)
