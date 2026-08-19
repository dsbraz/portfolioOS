"""The eval harness must be beyond suspicion.

When an agent evaluation fails, the question has to be "what did the agent do",
never "is the harness lying". So the snapshot/diff pair gets the same scrutiny
as production code.
"""

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.executive import Executive
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.startup import Startup, StartupStatus
from scripts.eval_state import descrever, diff, snapshot


async def _startup(session: AsyncSession) -> Startup:
    startup = Startup(
        name="Eval Co",
        status=StartupStatus.HEALTHY,
        sector="tech",
        investment_date=date(2026, 1, 1),
    )
    session.add(startup)
    await session.flush()
    return startup


@pytest.mark.asyncio
async def test_um_estado_imutavel_nao_produz_mudanca(session: AsyncSession):
    await _startup(session)

    antes = await snapshot(session)
    depois = await snapshot(session)

    # A leitura pura é o caso mais comum das skills; um falso positivo aqui
    # tornaria todo eval de leitura inútil.
    assert diff(antes, depois) == []
    assert descrever([]) == "nenhuma mudança"


@pytest.mark.asyncio
async def test_detecta_criacao(session: AsyncSession):
    startup = await _startup(session)
    antes = await snapshot(session)

    session.add(MonthlyIndicator(startup_id=startup.id, month=5, year=2026))
    await session.flush()

    mudancas = diff(antes, await snapshot(session))

    assert len(mudancas) == 1
    assert mudancas[0].tabela == "indicadores"
    assert mudancas[0].tipo == "criado"


@pytest.mark.asyncio
async def test_detecta_remocao(session: AsyncSession):
    startup = await _startup(session)
    indicador = MonthlyIndicator(startup_id=startup.id, month=5, year=2026)
    session.add(indicador)
    await session.flush()
    antes = await snapshot(session)

    await session.delete(indicador)
    await session.flush()

    mudancas = diff(antes, await snapshot(session))

    assert [m.tipo for m in mudancas] == ["removido"]


@pytest.mark.asyncio
async def test_detecta_alteracao_e_nomeia_o_campo(session: AsyncSession):
    startup = await _startup(session)
    indicador = MonthlyIndicator(startup_id=startup.id, month=5, year=2026)
    session.add(indicador)
    await session.flush()
    antes = await snapshot(session)

    indicador.headcount = 42
    await session.flush()

    mudancas = diff(antes, await snapshot(session))

    assert len(mudancas) == 1
    assert mudancas[0].tipo == "alterado"
    # O campo alterado aparece na mensagem: é o que diz ao humano o que o
    # agente mexeu.
    assert "headcount" in mudancas[0].campos
    assert "headcount" in descrever(mudancas)


@pytest.mark.asyncio
async def test_uma_escrita_silenciosa_nao_escapa(session: AsyncSession):
    """Regressão do risco central: uma skill de leitura que grava.

    Uma alteração que só mexe em `updated_at` continua sendo uma escrita — por
    isso esse campo NÃO é ignorado pelo diff.
    """
    startup = await _startup(session)
    antes = await snapshot(session)

    startup.notes = "tocado por quem não devia"
    await session.flush()

    mudancas = diff(antes, await snapshot(session))

    assert mudancas, "uma escrita passou despercebida pelo tripwire"
    assert mudancas[0].tabela == "startups"


@pytest.mark.asyncio
async def test_cobre_todas_as_tabelas_alcancaveis_pelo_produto(session: AsyncSession):
    """Uma tabela fora da lista é um ponto cego permanente."""
    from app.domain.models import Base
    from scripts.eval_state import TABELAS_OBSERVADAS

    observadas = {modelo.__tablename__ for _, modelo in TABELAS_OBSERVADAS}
    existentes = set(Base.metadata.tables) - {"alembic_version"}

    assert existentes <= observadas, (
        f"tabela sem observação no harness: {existentes - observadas}"
    )


@pytest.mark.asyncio
async def test_nao_confunde_registros_de_tabelas_diferentes(session: AsyncSession):
    startup = await _startup(session)
    antes = await snapshot(session)

    session.add(Executive(startup_id=startup.id, name="Ana", phone="+5511987650001"))
    await session.flush()

    mudancas = diff(antes, await snapshot(session))

    assert [m.tabela for m in mudancas] == ["executivos"]
