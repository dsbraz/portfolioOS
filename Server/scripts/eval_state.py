"""State snapshot and diff — the assertion half of the skill evaluations.

An agent evaluation cannot assert on the agent's prose: the wording changes
every run. What does not change is **what the agent did to the platform**, and
that is a fact the database holds.

So every eval follows the same shape:

    antes = await snapshot(session)
    ...  the agent runs a turn ...
    depois = await snapshot(session)
    mudancas = diff(antes, depois)

and then asserts on `mudancas` — usually that it is empty (a read-only skill, or
a write skill before its confirmation turn), sometimes that it contains exactly
one expected row.

This module holds no LLM and no network. It is deterministic and unit-tested,
so when an eval fails the harness is never the suspect.
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.board_meeting import BoardMeeting
from app.domain.models.deal import Deal
from app.domain.models.executive import Executive
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken
from app.domain.models.startup import Startup
from app.domain.models.user import User
from app.domain.models.user_invite import UserInvite

# Every table an agent could touch through the product. A skill that writes
# somewhere absent from this list would slip past the tripwire, so adding a
# table to the domain means adding it here.
TABELAS_OBSERVADAS = (
    ("startups", Startup),
    ("indicadores", MonthlyIndicator),
    ("links", MonthlyIndicatorToken),
    ("reunioes", BoardMeeting),
    ("executivos", Executive),
    ("negocios", Deal),
    ("usuarios", User),
    ("convites", UserInvite),
)

# Columns that move on their own and would drown a diff in noise. `updated_at`
# is deliberately NOT here: an update that changes nothing but the timestamp is
# still a write, and catching it is the point.
_IGNORADAS = frozenset({"hashed_password"})


@dataclass(frozen=True)
class Mudanca:
    """One row that appeared, vanished, or changed."""

    tabela: str
    tipo: str  # "criado" | "removido" | "alterado"
    id: str
    campos: tuple[str, ...] = ()

    def __str__(self) -> str:
        detalhe = f" ({', '.join(self.campos)})" if self.campos else ""
        return f"{self.tipo} em {self.tabela}: {self.id}{detalhe}"


def _linha(registro: Any) -> dict[str, Any]:
    colunas = registro.__table__.columns.keys()
    return {
        coluna: str(getattr(registro, coluna))
        for coluna in colunas
        if coluna not in _IGNORADAS
    }


async def snapshot(session: AsyncSession) -> dict[str, dict[str, dict[str, Any]]]:
    """Every observed row, keyed by table then id."""
    estado: dict[str, dict[str, dict[str, Any]]] = {}
    for nome, modelo in TABELAS_OBSERVADAS:
        resultado = await session.execute(select(modelo))
        estado[nome] = {
            str(registro.id): _linha(registro) for registro in resultado.scalars().all()
        }
    return estado


def diff(
    antes: dict[str, dict[str, dict[str, Any]]],
    depois: dict[str, dict[str, dict[str, Any]]],
) -> list[Mudanca]:
    """What changed between two snapshots, in a stable order."""
    mudancas: list[Mudanca] = []

    for tabela, _ in TABELAS_OBSERVADAS:
        linhas_antes = antes.get(tabela, {})
        linhas_depois = depois.get(tabela, {})

        for identificador in sorted(set(linhas_depois) - set(linhas_antes)):
            mudancas.append(Mudanca(tabela, "criado", identificador))

        for identificador in sorted(set(linhas_antes) - set(linhas_depois)):
            mudancas.append(Mudanca(tabela, "removido", identificador))

        for identificador in sorted(set(linhas_antes) & set(linhas_depois)):
            campos = tuple(
                campo
                for campo, valor in linhas_depois[identificador].items()
                if linhas_antes[identificador].get(campo) != valor
            )
            if campos:
                mudancas.append(
                    Mudanca(tabela, "alterado", identificador, campos)
                )

    return mudancas


def descrever(mudancas: list[Mudanca]) -> str:
    """A failure message a person can act on."""
    if not mudancas:
        return "nenhuma mudança"
    return "\n".join(f"  - {mudanca}" for mudanca in mudancas)
