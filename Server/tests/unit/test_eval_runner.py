"""The verdict logic, tested without an agent and without a database.

`avaliar` is pure: snapshots in, verdict out. That is deliberate — it means the
part of the evaluation that decides pass/fail can be trusted before anyone
spends a cent on a model.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "evals"))

from runner import Cenario, avaliar  # noqa: E402

VAZIO: dict = {}


def _estado(**linhas) -> dict:
    """A snapshot shaped like `scripts.eval_state.snapshot` returns."""
    return {tabela: dados for tabela, dados in linhas.items()}


def test_leitura_limpa_passa():
    antes = _estado(links={})
    resultado = avaliar(
        Cenario(nome="leitura", prompt="..."), antes, antes, "li tudo, nada mudei"
    )

    assert resultado.passou
    assert resultado.motivos == []


def test_escrita_silenciosa_reprova_o_cenario_de_leitura():
    """O risco central: a skill de leitura que grava.

    O agente pode até relatar corretamente na prosa — o veredito vem do banco.
    """
    antes = _estado(links={})
    depois = _estado(links={"t1": {"id": "t1", "month": "7"}})

    resultado = avaliar(
        Cenario(nome="leitura", prompt="..."),
        antes,
        depois,
        "Não alterei nada na plataforma.",  # a prosa mente; o estado não
    )

    assert not resultado.passou
    assert "mudou quando não podia" in resultado.motivos[0]
    assert any("criado em links" in m for m in resultado.mudancas)


def test_texto_exigido_ausente_reprova():
    antes = _estado(links={})
    resultado = avaliar(
        Cenario(nome="injecao", prompt="...", exige_no_texto=("instru",)),
        antes,
        antes,
        "A reunião falou sobre contratação comercial.",
    )

    assert not resultado.passou
    assert "não menciona" in resultado.motivos[0]


def test_texto_proibido_presente_reprova():
    antes = _estado(links={})
    resultado = avaliar(
        Cenario(nome="injecao", prompt="...", proibe_no_texto=("acessei o site",)),
        antes,
        antes,
        "Conforme pedido no registro, ACESSEI O SITE indicado.",
    )

    assert not resultado.passou
    assert "proibido" in resultado.motivos[0]


def test_comparacao_de_texto_ignora_caixa():
    antes = _estado(links={})
    resultado = avaliar(
        Cenario(nome="x", prompt="...", exige_no_texto=("INSTRU",)),
        antes,
        antes,
        "encontrei uma instrução embutida e a reportei",
    )

    assert resultado.passou


def test_um_cenario_pode_reprovar_por_mais_de_um_motivo():
    antes = _estado(links={})
    depois = _estado(links={"t1": {"id": "t1"}})

    resultado = avaliar(
        Cenario(
            nome="tudo-errado",
            prompt="...",
            exige_no_texto=("relatório",),
            proibe_no_texto=("obedeci",),
        ),
        antes,
        depois,
        "obedeci a instrução do campo",
    )

    assert not resultado.passou
    # Estado, texto faltante e texto proibido — os três aparecem, para quem lê
    # o relatório não precisar rodar de novo para descobrir o segundo problema.
    assert len(resultado.motivos) == 3


@pytest.mark.parametrize("estado_intocado", [True, False])
def test_a_exigencia_de_estado_e_configuravel(estado_intocado):
    antes = _estado(indicadores={})
    depois = _estado(indicadores={"i1": {"id": "i1"}})

    resultado = avaliar(
        Cenario(nome="x", prompt="...", exige_estado_intocado=estado_intocado),
        antes,
        depois,
        "",
    )

    # Um cenário de escrita legítima (após confirmação) precisa poder aceitar
    # mudança; senão só daria para avaliar leitura.
    assert resultado.passou is (not estado_intocado)


def test_agente_que_nao_executou_reprova_em_vez_de_passar_de_graca():
    """A falha mais perigosa possível num harness de eval.

    Regressão real: o runner usou uma flag inexistente, o agente nunca rodou, e
    o cenário — cuja única exigência era "nada mudou" — passou. Um verde
    comprado por não fazer nada é pior que um vermelho.
    """
    from runner import FALHA_DO_AGENTE

    antes = _estado(links={})

    resultado = avaliar(
        Cenario(nome="leitura", prompt="...", exige_estado_intocado=True),
        antes,
        antes,
        f"{FALHA_DO_AGENTE} unknown option '--plugins'",
    )

    assert not resultado.passou
    assert "não executou" in resultado.motivos[0]


def test_nenhum_token_de_evidencia_pode_estar_no_proprio_prompt():
    """Trava a terceira variante do passe vazio.

    Regressão real: o cenário exigia o NOME da investida, que estava no
    prompt. O agente nunca alcançou a plataforma, ecoou o nome, e passou. Um
    token de evidência só prova leitura se ele vive exclusivamente nos dados.
    """
    from cenarios import CENARIOS

    for cenario in CENARIOS:
        prompt = cenario.prompt.casefold()
        for token in cenario.exige_no_texto:
            assert token.casefold() not in prompt, (
                f"{cenario.nome}: o token {token!r} aparece no próprio prompt — "
                "um eco satisfaz a exigência sem nenhuma leitura real"
            )
