import uuid
from decimal import Decimal

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken


def period_expression():
    """`ano * 100 + mes` como inteiro comparavel e ordenavel (202607).

    Dispensa comparar dois campos e evita o classico de Dez/2025 vencer
    Jan/2026 por ter mes maior.

    Os DOIS casts sao necessarios, nao decorativos: `year` e `month` sao
    SMALLINT, e o tipo da soma segue o ultimo operando. Convertendo so o `year`,
    o literal da comparacao ainda saia como int16 -- 202607 estoura o limite de
    32767 e o asyncpg recusa o parametro em runtime.
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

    async def create(self, indicator: MonthlyIndicator) -> MonthlyIndicator:
        self._session.add(indicator)
        await self._session.flush()
        await self._session.refresh(indicator)
        return indicator

    async def update(self, indicator: MonthlyIndicator) -> MonthlyIndicator:
        await self._session.flush()
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
    ) -> dict[uuid.UUID, tuple[int, int]]:
        """Ultimo periodo reportado por startup, ATE o periodo consultado.

        O limite superior importa: olhando Fev/2026, um reporte de Jul/2026 e
        futuro em relacao ao recorte da tela, e exibi-lo diria que a startup
        reportou algo que, naquele contexto, ainda nao aconteceu.

        Retorna `(ano, mes)`; startups sem nenhum reporte ficam fora do dict.
        """
        if not startup_ids:
            return {}

        period = period_expression()

        result = await self._session.execute(
            select(MonthlyIndicator.startup_id, func.max(period))
            .where(
                MonthlyIndicator.startup_id.in_(startup_ids),
                period <= year * 100 + month,
            )
            .group_by(MonthlyIndicator.startup_id)
        )

        return {
            row[0]: (row[1] // 100, row[1] % 100)
            for row in result.all()
            if row[1] is not None
        }

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

    async def create_token(self, token: MonthlyIndicatorToken) -> MonthlyIndicatorToken:
        self._session.add(token)
        await self._session.flush()
        await self._session.refresh(token)
        return token
