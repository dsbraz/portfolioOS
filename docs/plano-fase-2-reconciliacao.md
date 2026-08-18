# Plano de implementação — Fase 2 (reconciliação documental)

- **Branch:** `feat/ia-na-plataforma`
- **Fonte normativa:** [plano de desenvolvimento](plano-desenvolvimento-prds.md) §Fase 2 e §12
- **Última atualização:** 2026-08-18
- **Natureza:** artefato de trabalho — pode ser apagado quando a fase fechar.

> As âncoras `file:line` abaixo foram **reverificadas em 2026-08-18**, após o
> fechamento da Fase 1 (commits até `ebcaa35`). Onde o plano-mestre citava
> linhas que a Fase 1 moveu, o valor aqui já é o atual. Confirme de novo antes
> de editar — docs mudam a cada passo desta própria fase.

## 0. Regras da fase

1. **Nenhuma decisão de humano.** A transição de status `Rascunho`/`Em
   revisão` → aprovado é do Daniel Braz (plano-mestre §11) e **fica fora**
   desta fase. O mesmo vale para remover ou reter a rota
   `GET /api/skills/{name}.zip` — aqui ela só é **registrada** como decisão
   aberta.
2. **Direção do drift: doc → código.** Onde RFC e código divergem em nomes, o
   código entregue, testado e commitado vence; a RFC é atualizada. Renomear
   código estável para casar com prosa não tem valor de produto.
3. **Preservar o registro histórico.** O §7 da RFC-002 é o único registro de
   que os incrementos 1–2 saíram — anotar status por passo, nunca apagar.
4. Idioma dos documentos: manter o idioma que cada trecho já usa (os docs
   misturam PT-BR e EN-US por seção); mensagens de commit em PT-BR.

## 1. RFC-001 (`docs/rfc/001-adicao-unificada-de-indicador.md`)

### 1.1 §3.1 — símbolos prescritos vs. entregues

A RFC prescreve `models/whatsapp-share.ts` com `normalizePhoneBR`,
`buildWhatsAppShareUrl`, `buildIndicatorInviteMessage` (`:114-117`, `:193`,
`:198`, `:348`). O código entregou `models/whatsapp.ts` com
`normalizeBrazilianPhone`, `formatBrazilianPhone`, `firstName`,
`buildIndicatorRequestMessage`, `buildWhatsAppLink`
(`Client/src/app/models/whatsapp.ts:18-62`). **Atualizar a RFC para os nomes
do código** (regra 0.2). A metade `models/indicator-form.ts` já bate — a
Fase 1 a criou com o nome que a RFC pede; nada a fazer.

### 1.2 "Segredo portador" ×3

`:97` (glossário), `:187` (§3.3), `:374` (tabela de riscos). Reescrever nos
termos da decisão de 14/08 (PRD-002 pendência 6, PRD-001 §7): *capacidade de
escrita num único período, entregue só ao contato cadastrado* — não segredo,
não credencial. No glossário (`:97`), a definição vira algo como "capacidade
de escrita pública na zona reportada de um período; entregue só ao contato
cadastrado". Em `:374`, o risco continua válido (número errado recebe o link),
só o parêntese "(segredo portador)" muda.

### 1.3 §4 — teto de headcount ausente

A tabela de contrato diz `headcount | inteiro | >= 0, inteiro` e omite o teto
`2_147_483_647` que o backend impõe
(`Server/app/domain/schemas/monthly_indicator.py:16`) e o cliente espelha
(`Client/src/app/models/indicator-form.ts:20`). Acrescentar o limite superior
à linha.

### 1.4 §8 — status por incremento

Ler o §8 inteiro e: (a) remover qualquer marcador "pendente" sobre a extinção
do `token-generate-dialog` — ele foi removido na Fase 1 (`:122` já descreve
"← REMOVIDO", agora verdadeiro; `:324` cita os specs removidos); (b) corrigir
o status por incremento para o estado real pós-Fase 1: itens 1–5 do PRD-001
entregues, jornadas 6.1–6.5 marcadas.

### 1.5 §3.3 — destinatário (verificação, provavelmente ok)

O texto atual já diz "escolhido entre os executivos da startup" (`:35-36`,
`:184-190`) e o nome acessível `:221-222` já bate com o código pós-`f6d1c33`.
Conferir e não mexer se estiver alinhado.

## 2. PRD-001 (`docs/prd/001-adicao-unificada-de-indicador.md`)

### 2.1 "Segredo portador" ×2

`:49` (resumo) e `:207` (regras da jornada 6.5) contradizem o §7 do próprio
documento (`:239`, que já registra a decisão de 14/08). Reescrever os dois
trechos na linguagem de capacidade de escrita. Em `:207`, a justificativa da
prévia obrigatória deixa de ser "a mensagem carrega um segredo" e passa a ser
"quem possui o link escreve no período".

### 2.2 Data de cabeçalho

`:7` diz 2026-08-11; o conteúdo registra 14/08 (`:239`) e as jornadas foram
marcadas em 18/08. Corrigir para a data desta edição.

**Não** alterar o campo Status (regra 0.1).

## 3. PRD-002 / RFC-002

### 3.1 Texto normativo ensina o oposto da decisão

Três pontos ainda mandam a página `/ia` ensinar que o link é segredo:

- `docs/rfc/002-ia-na-plataforma.md:287` — "indicator links are secrets"
- `docs/rfc/002-ia-na-plataforma.md:469` — "secret indicator links"
- `docs/prd/002-ia-na-plataforma.md:202` — "indicator links are secrets"

A decisão de 14/08 está registrada nos mesmos docs (PRD-002 `:393`, `:482`;
RFC-002 `:606`) e a página entregue já ensina o certo
(`Client/src/app/pages/ai/ai.html:88`: "O link de indicador permite escrever
no período — envie apenas ao contato cadastrado"). Alinhar os três trechos
normativos com a decisão e com a página.

### 3.2 "As três skills" → contagem real

- `docs/rfc/002-ia-na-plataforma.md:306` — "As três skills passam a usar o
  mesmo cabeçalho": são cinco no repositório (quatro publicadas +
  `auditoria-qualitativa` bloqueada). Reescrever sem número mágico
  (ex.: "todas as skills do pacote") ou com a contagem certa.
- `:490` — "o passo inicial de todas as três skills" — cai junto com o item
  3.4 abaixo.

### 3.3 §5 — tabela de nomes acessíveis (`:482-488`)

Estender em três direções:

1. **`cobrar-indicadores`** — a própria regra da RFC ("skill nova obriga a
   estendê-la", `:499`) exige. Vocabulário fixado por
   `Server/tests/unit/test_skills_lint.py:203-205` e pelo SKILL.md: "Adicionar
   indicador", diálogo "Adicionar indicador — {Mmm/AAAA}", modo "Gerar link
   para a investida", botão "Gerar link", painel com "Enviar por WhatsApp
   para {nome}", "Copiar link de {Mmm/AAAA}".
2. **`operar-portfolioos`** — a skill base por onde tudo roteia não tem linha
   na tabela. Vocabulário em
   `Server/skills/operar-portfolioos/references/monitoring.md` (ex.: "Ver
   reunião de {...}", "Ver executivo {...}", "Ações de {...}", "Ações do
   indicador de {period}").
3. **Nomes que a Fase 1 mudou** — a linha "Detalhe da startup" cita os botões
   antigos; hoje a entrada é uma só ("Adicionar indicador" abre o diálogo
   unificado). Conferir cada nome da tabela contra o DOM atual.

### 3.4 §5 — fragilidade da linha clicável (`:490-496`)

O parágrafo declara a linha de monitoramento como "fragilidade real,
registrada em §9" — mas (i) o código já corrigiu: a linha carrega um link real
nomeado pela startup (`portfolio.html`, `href="/startup/{id}"`, padrão
row-opener), e (ii) o §9 **não tem** essa linha (xref pendurada — verificado
por grep em 18/08). Reescrever o parágrafo para registrar a correção e
remover a referência ao §9.

### 3.5 §10 — roteiro sem item de cobrança

A linha 6.7 (`:585`) afirma verificação "no roteiro manual", mas o roteiro
(a)–(g) (`:583`) não tem item de cobrança. **Adicionar o item (h)** ao
roteiro: fila conferida contra `last_reported`, prévia exibida, nenhum envio
sem confirmação, startup sem telefone bloqueada com orientação. (Alternativa
de menor valor: corrigir só a linha de rastreabilidade — não usar.)

### 3.6 §7 — status por passo do rollout

Passos 1–4 (`:seção "Compatibility and rollout"`) entregues mas escritos como
futuro; passo 5 (validação com usuário real) nunca rodou. Anotar o status em
cada passo — ex.: sufixo "✅ entregue (inc. 1, 2026-08-1x)" nos passos 1–4 e
"pendente" no 5 — preservando o texto original (regra 0.3).

### 3.7 Datas de cabeçalho

- PRD-002 `:7` (2026-08-13) < decisão de 14/08 em `:482`.
- RFC-002 `:8` (2026-08-13) < decisão de 14/08 em `:606`.

Corrigir ambos para a data desta edição.

## 4. Planos e AGENTS.md

### 4.1 `docs/plano-incremento-1-ia.md`

- Marcar como **histórico/concluído** no cabeçalho (o incremento 1 fechou; o
  próprio doc se declara descartável).
- `:96` — "two product routes, `/api/skills` and `/api/skills.zip`" → são
  **três**: `/skills.zip` (`skill_controller.py:39`), `/skills/{name}.zip`
  (`:63`) e o catálogo. Corrigir a frase e listar as três.

### 4.2 AGENTS.md — seção *Machine-readable UI*

Os PRDs citam a seção como contrato de operabilidade (PRD-001 `:250`, `:305`;
PRD-002 `:8`, `:429`, `:506`) para regras que ela não contém. A seção já tem
nomes de ação de linha; **faltam duas regras** que os PRDs assumem:

1. **Linha clicável = link nomeado** (padrão row-opener): toda linha de tabela
   que navega carrega um link real com o nome da entidade — nunca só um
   handler de clique na `<tr>`.
2. **Painel de link com o valor visível como texto**: nenhum fluxo depende da
   área de transferência; a cópia é conveniência tolerante a falha.

Adicionar as duas ao AGENTS.md **e** ao espelho em CLAUDE.md (as seções são
gêmeas — atualizar um só desincroniza).

### 4.3 Rota individual `GET /api/skills/{name}.zip` — registrar, não decidir

Existe (`skill_controller.py:63-88`), contradiz a RFC-002 §4 ("one complete
package") e nenhum cliente a consome. Adicionar linha à tabela §11 da
RFC-002: "Rota individual `/skills/{name}.zip`: remover ou reter | aberta —
Produto". Nada além disso (regra 0.1).

## 5. Ordem de execução e commits

A ordem minimiza retrabalho (cada doc é tocado uma vez):

| # | Passo | Commit sugerido |
|---|---|---|
| 1 | Itens 1.1–1.5 + 2.1–2.2 (RFC-001 e PRD-001) | `docs: reconciliar RFC-001 e PRD-001 com o código entregue` |
| 2 | Itens 3.1–3.7 (PRD-002 e RFC-002) | `docs: atualizar PRD-002 e RFC-002 pós-incrementos 1 e 2` |
| 3 | Itens 4.1–4.3 (planos, AGENTS.md, CLAUDE.md, §11 RFC-002) | `docs: marcar o plano do incremento 1 como histórico e completar o contrato de operabilidade` |

O item 4.3 edita a RFC-002 de novo — se preferir um toque só por arquivo,
mover 4.3 para o commit 2.

## 6. Fecho da fase (gate do plano-mestre §12)

A fase fecha quando **todos** valem:

1. `grep -rn "segredo portador" docs/prd docs/rfc` → vazio.
2. `grep -n "três skills\|todas as três" docs/rfc/002-*.md` → nenhum uso
   normativo com contagem errada.
3. `grep -n "two product routes" docs/` → vazio.
4. `grep -rn "token-generate" docs/prd docs/rfc` → só menções históricas
   explícitas ("← REMOVIDO"), nenhum marcador pendente.
5. Datas de "Última atualização" ≥ data do conteúdo mais novo de cada doc.
6. RFC-002 §5 cobre `cobrar-indicadores` e `operar-portfolioos`; §7 tem
   status por passo; §10 tem item de cobrança; a xref §5→§9 não existe mais.
7. Nenhum status de aprovação foi alterado (diff dos campos `Status:` vazio).
