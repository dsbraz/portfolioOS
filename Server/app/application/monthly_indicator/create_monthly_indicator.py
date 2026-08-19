from app.domain.exceptions import ConflictError
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.validators import validate_period_not_future
from app.repositories.monthly_indicator_repository import (
    MonthlyIndicatorRepository,
)

_REPORTED_FIELDS = (
    "total_revenue",
    "recurring_revenue_pct",
    "gross_margin_pct",
    "cash_balance",
    "headcount",
    "ebitda_burn",
    "achievements",
    "challenges",
    "comments",
)


class CreateMonthlyIndicator:
    def __init__(self, repository: MonthlyIndicatorRepository) -> None:
        self._repository = repository

    async def execute(self, indicator: MonthlyIndicator) -> MonthlyIndicator:
        validate_period_not_future(indicator.month, indicator.year)

        existing = await self._repository.get_by_startup_and_period(
            indicator.startup_id, indicator.month, indicator.year
        )
        if existing:
            return await self._merge(indicator, existing)

        try:
            return await self._repository.create(indicator)
        except ConflictError:
            # Lost the insert race: another writer created this period between
            # the check above and the insert. The intent is "this period should
            # carry these values", so merge onto the row that landed instead of
            # failing a write the caller reasonably expects to succeed.
            winner = await self._repository.get_by_startup_and_period(
                indicator.startup_id, indicator.month, indicator.year
            )
            if winner is None:
                raise
            return await self._merge(indicator, winner)

    async def _merge(
        self, incoming: MonthlyIndicator, target: MonthlyIndicator
    ) -> MonthlyIndicator:
        """Field by field, absence never erases (PRD-001 §6.1/§8)."""
        for field in _REPORTED_FIELDS:
            value = getattr(incoming, field)
            if value is not None:
                setattr(target, field, value)
        return await self._repository.update(target)
