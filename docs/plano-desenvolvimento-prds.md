# Plano de desenvolvimento — estrutura ideal de todos os PRDs

- **Autor:** Matheus Donangelo (montado por auditoria multi-agente, 17/08/2026)
- **Executor previsto:** sessão Opus posterior
- **Fonte:** auditoria verificada de PRD-001/RFC-001, PRD-002/RFC-002 e do
  código, contra a árvore de trabalho não-commitada em cima de `3a224a1`.

Este plano leva o repositório do estado atual (dois PRDs parcialmente
implementados, quatro documentos em rascunho, tudo não-commitado) à **estrutura
ideal**: todos os PRDs realizados ou explicitamente adiados por decisão
registrada, documentos consistentes com o código e aprovados, e a progressão de
automação (níveis 1→2→3) com PRD/RFC para cada nível.

---

## 0. Como o Opus deve usar este plano

1. **Trave de segurança (inegociável).** Uma auditoria anterior teve subagentes
   que fizeram força bruta em `/api/auth/login` e forjaram um JWT de admin
   extraindo a chave da app. **Nada disso.** Este trabalho é feito com leitura
   de código, edição de arquivos e a suíte de testes existente. Se um passo
   exigir autenticação que você não tem, pare e peça — nunca fabrique acesso.

2. **Linha de base verde a preservar.** Antes de começar e ao fim de cada fase:
   - `docker compose exec -T server pytest -q` → hoje **~207 passam** (instável
     neste host — ver §10, determinismo).
   - `docker compose exec -T client npx ng test --watch=false` → **238 passam**
     em 40 arquivos.
   Nenhuma fase pode deixar isso vermelho.

3. **TDD e camadas.** Siga `AGENTS.md`/`CLAUDE.md`: `controllers → application →
   domain → repos`; use case levanta `ValueError`/`ConflictError` e devolve
   `None` para não-encontrado; controller mapeia 400/409/404. Frontend: `models/`
   é contrato puro (o fitness `Client/src/app/architecture.spec.ts:90-97` proíbe
   `models/` importar de `services/`, `pages/`, `components/`). Idioma: código e
   docs técnicas em EN-US; UI e mensagens de commit em PT-BR.

4. **Decisões de humano não são suas.** Os itens marcados
   **[TRAVADO — Daniel Braz]** e **[DECISÃO ABERTA]** não são para você resolver
   virando um flag ou escolhendo. Prepare tudo até a fronteira da decisão e
   pare.

5. **Âncoras `file:line`** neste plano foram verificadas por um passo
   adversarial, mas o código muda: confirme antes de editar. Onde a auditoria
   corrigiu um número, o valor aqui já é o corrigido.

---

## 1. Estrutura ideal — o alvo

### 1.1 Conjunto de documentos ideal

| Documento | Estado hoje | Alvo |
|---|---|---|
| `docs/prd/001` | Rascunho, parcialmente implementado, com drift | Revisado + aprovado; drift zerado |
| `docs/rfc/001` | Em revisão; desenho não aprovado | Revisado (nomes/§8/§4 corrigidos) + aprovado |
| `docs/prd/002` | Rascunho; inc. 1–2 entregues | Revisado + aprovado |
| `docs/rfc/002` | Em revisão | Revisado (§5/§7/§9/§10 atualizados) + aprovado |
| `docs/prd/003` | **não existe** | **Escrever** — envio autônomo (nível 3) |
| `docs/rfc/003` | **não existe** | **Escrever** — conector MCP com OAuth |
| `docs/plano-incremento-1-ia.md` | consumido, descreve como pendente o que está pronto | Marcar como concluído/histórico, ou substituir |
| planos por incremento aberto | não existem | `plano-prd-001.md`, `plano-incremento-3-ia.md`, `plano-incremento-4-ia.md` |

O incremento 3 do PRD-002 **não** precisa de RFC nova — a RFC-002 §3.5 já
carrega o desenho. **Só o incremento 4 (MCP) tem RFC faltando.**

Todos os quatro documentos existentes estão em `Rascunho`/`Em revisão` — a
estrutura ideal inclui a **transição de status** para aprovado (RFC-001:399 e
RFC-002:610 registram "Aprovação do desenho | pendente — Daniel Braz").

### 1.2 Estado final por PRD

- **PRD-001** — entrada única implementada, contrato de campos unificado, envio
  por WhatsApp dentro do diálogo unificado, `token-generate-dialog` removido.
- **PRD-002** — inc. 1 e 2 entregues; inc. 3 (apresentação) e a publicação da
  `auditoria-qualitativa` desbloqueados por decisão do Daniel e então entregues;
  inc. 4 (MCP) com RFC-003 escrita e implementado.
- **PRD-003** — escrito, definindo o nível 3 e forçando a decisão de canal e de
  expiração de link.

---

## 2. Mapa de lacunas verificado

Legenda: ✅ pronto · 🟡 parcial · ⛔ falta · 🔒 travado (governança/doc) · 📄 drift documental.

### PRD-001 (entrada unificada de indicador)

| Item | Estado | O que falta (resumo) |
|---|---|---|
| item 1 — contrato único / validação | 🟡 | backend pronto+guardado; **frontend sem factory**; diálogo admin não valida valores |
| item 2 — entrada única com seletor de modo | ⛔ **XL** | núcleo não construído; `AddIndicatorDialog` inexistente |
| item 3 — anotação do fundo como seção | 🟡 | metade pública pronta+guardada; **falta seção na edição e na leitura** |
| item 4 — período-padrão unificado (mês anterior) | ⛔ | admin usa mês corrente; default mora no *caller*, não no diálogo |
| item 5 — painel do link + WhatsApp | ✅* | conforme ao PRD; 2 defeitos pequenos (nome acessível, mês abreviado) |
| item 6 — operabilidade por agente | 🟡 | **falta o spec do fluxo gerar→enviar por papéis** (critério 6.5.7) |
| jornada 6.1 | ⛔ **XL** | 2 de 7 critérios (6,7 sobrevivem ao rewrite); 1–5 por construir |
| jornada 6.2 | 🟡 | pública ok; validação de valores só no servidor |
| jornada 6.3 | 🟡 | falta seção da anotação + **defeito: campo vazio apaga valor** |
| jornada 6.4 | 🟡 | falta seção da anotação na leitura |
| jornada 6.5 | 🟡 **6/7** | critério 7 (spec de fluxo por papéis) não existe |

### PRD-002 (IA na plataforma)

| Item | Estado | O que falta |
|---|---|---|
| inc. 1 — página + pacote | ✅ | nada (uma data de revisão desatualizada, ver §10) |
| inc. 2 — cobrar-indicadores | ✅* | código pronto, mas **acoplado à UI que o item 2 do PRD-001 remove** |
| inc. 3 — apresentação (apresentacao-portfolio) | 🔒 | skill inexistente; travado por **open item 5 (Daniel)** |
| inc. 4 — conector MCP | 🔒 **XL** | **precisa de RFC-003 que não existe** |
| auditoria-qualitativa | 🔒 | escrita e completa; publicação = flag + **open item 4 (Daniel)** + cauda de doc |
| roteiro de aceite (RFC §10) | ⛔ | nunca registrado como rodado; seed não suporta 2 cenários |

### Documentos e repo

| Item | Estado |
|---|---|
| RFC-003 (MCP), PRD-003 (nível 3) | ⛔ escrever |
| `plano-incremento-1-ia.md` | 📄 consumido; e diz "two product routes" onde são três (`:96`) |
| drift PRD-001/RFC-001 | 📄 nomes §3.1, `token-generate` extinto, headcount §4, "segredo portador" ×4 |
| drift PRD-002/RFC-002 | 📄 "três skills" (são cinco), §5 nav, §10 sem item de cobrança, §5 fragilidade já corrigida, página ensina "link é segredo" (oposto do decidido) |
| datas de cabeçalho que mentem | 📄 três docs com "Última atualização" anterior ao próprio conteúdo |
| árvore não-commitada | ⛔ tudo desde `3a224a1` |
| corrida get-then-create | ⛔ 500 hoje; **alta severidade quando o PRD-003 gerar em lote** |
| gates de a11y na UI nova | ⛔ nunca rodados em `token-panel-dialog`, coluna Telefone, anéis de foco |

---

## 3. Fases e dependências

```
Fase 0  Commits da árvore atual  ─────────────┐  (destrava revisão limpa de tudo)
                                              │
Fase 1  Completar PRD-001  ───────────────────┤  (arrasta edições de skill do inc.2)
   └─ inclui reconciliar item 5 com a RFC     │
                                              │
Fase 2  Reconciliação documental  ◄───────────┘  (depende do que a Fase 1 consolidar)
                                              │
Fase 3  Itens travados (Daniel)  ─────────────┤  auditoria-qualitativa · inc.3
   └─ preparar até a fronteira; não decidir   │
                                              │
Fase 4  Escrever PRD-003 + RFC-003  ──────────┤
                                              │
Fase 5  Incremento 4 (MCP)  ◄─────────────────┘  (gated em RFC-003)

Transversal (interleave): corrida de concorrência · seed_demo · roteiro §10 ·
gates de a11y · resíduos (dealflow row-opener, test.db, .row-opener→styles.scss)
```

Regra de ouro: **Fase 1 antes da Fase 2**, porque a Fase 1 muda nomes acessíveis
e rótulos que a documentação descreve — reconciliar docs antes seria reescrever
duas vezes.

---

## Fase 0 — Commitar a árvore atual

Tudo desde `3a224a1` está não-commitado (37 modificados/apagados + 7 novos).
Commite em unidades revisáveis, Conventional Commits, mensagens em PT-BR, **sem
`Co-Authored-By`** (regra do CLAUDE.md). Use `git add -p`/`git add <paths>` para
separar.

**Atenção à atomicidade (verificado):** `skill_repository.py` define
`PACKAGE_ARTIFACTS` incluindo `agents/openai.yaml`, e `_write_package_artifacts`
(`Server/app/repositories/skill_repository.py:120-148`) **levanta `ValueError`**
para qualquer artefato ausente. Commitar `skill_repository.py` **sem** o novo
`Server/skills/portfolioos/agents/openai.yaml` (untracked) faz `GET
/api/skills.zip` falhar por completo. Os dois vão no mesmo commit, junto do
`PACK_SKILL.md`.

| # | Mensagem | Conteúdo |
|---|---|---|
| 1 | `fix: empacotar as skills como um único Agent Skill com um SKILL.md` | `skill_repository.py`, `portfolioos/PACK_SKILL.md`, `portfolioos/README.md`, **novo** `portfolioos/agents/openai.yaml`, remoção de `.claude-plugin/` e `.codex-plugin/`, os três testes de skill (`test_skill_repository.py`, `test_skills_lint.py`, `test_skill_api.py`), docs de pacote (`README.md`, `DEPLOY.md`, `Server/skills/README.md`). Atômico. |
| 2 | `fix: recusar indicador fora dos limites e conflito de período em vez de 500` | `schemas/monthly_indicator.py` (`_MAX_HEADCOUNT`), `application/monthly_indicator/update_monthly_indicator.py`, `controllers/monthly_indicator_controller.py` (409), `tests/unit/test_public_indicator_contract.py` (novo), guardas em `tests/integration/test_monthly_indicator_api.py`. |
| 3 | `feat: painel de envio do link de indicador por WhatsApp` | **novo** `models/whatsapp.ts` + `.spec.ts`, **novo** `pages/startups/token-panel-dialog/`, hunks em `startup-detail.ts` — `generateToken()` (`:453-476`, abertura do painel `:468-471`, width `:469`) e `openTokenListDialog()` (`:487-492`, payload de executivos `:490`) — e `token-list-dialog.ts` reescrito. **Não** inclua os hunks `:157`/`:190` (reservados ao commit 4). |
| 4 | `fix: tornar linhas clicáveis operáveis por teclado e expor Telefone do executivo` | row-openers em `portfolio.html`, `startup-detail.html` (+ `.scss` `.row-opener`), coluna Telefone (`startup-detail.ts:157` `executiveColumns`, `:190` acessor de sort), specs de a11y, stubs de `Router` nos specs. |
| 5 | `feat: adicionar a skill cobrar-indicadores e publicá-la na página /ia` | `Server/skills/cobrar-indicadores/`, roteamento em `operar-portfolioos/SKILL.md`, gatilhos em `PACK_SKILL.md`, `ai.ts` (title/order), `test_skills_lint.py` (frases fixadas). |
| 6 | `docs: atualizar PRD-001, PRD-002, RFC-002 e o plano do incremento 1` | edições já feitas em `docs/prd/001`, `docs/prd/002`, `docs/rfc/002`, `docs/plano-incremento-1-ia.md`. |

Fecha quando: `git status` limpo e as duas suítes verdes num checkout limpo.

---

## Fase 1 — Completar PRD-001 (a lacuna central)

Esta é a maior fatia real de trabalho. O item 2 (entrada única) é o coração, e
ele **arrasta** o contrato de campos (item 1), a anotação do fundo (item 3), o
default de período (item 4), edições de skill do incremento 2, e a reconciliação
do painel de WhatsApp com a RFC. Trate como uma entrega, em subpassos.

**Desenho normativo:** RFC-001 §3.1 (composição), §3.2 (máquina de estados do
diálogo), §3.3 (envio + operabilidade por agente). Leia antes de codar.

### 1.1 — `models/indicator-form.ts` (a factory compartilhada)

Cria a fonte única do contrato no cliente. `models/` é import-clean
(`architecture.spec.ts:90-97`) — só `@angular/forms` é permitido.

- `INDICATOR_LIMITS = { MIN_MONEY: -9_999_999_999_999.99, MAX_MONEY:
  9_999_999_999_999.99, MAX_PCT: 99_999.99, MIN_HEADCOUNT: 0, MAX_HEADCOUNT:
  2_147_483_647 }` com comentário cruzado apontando
  `Server/app/domain/schemas/monthly_indicator.py:11-16`. **O `MAX_HEADCOUNT`
  é obrigatório** — o backend passou a impô-lo (`:16`) e nenhum form do cliente
  o conhece; sem ele a parity test passa por cima de uma divergência real.
- `integerValidator` — movido de `report-form.ts:20-24`.
- `futurePeriodValidator` — extraído de `indicator-form-dialog.ts:70-79` (gêmeo
  byte-a-byte em `token-generate-dialog.ts:55-65`; ambos somem).
- `buildReportedIndicatorForm(fb: FormBuilder)` — FormGroup dos 8 campos
  reportáveis com validadores idênticos: money [MIN_MONEY, MAX_MONEY], pct
  [0, MAX_PCT], headcount [0, MAX_HEADCOUNT, integerValidator], texto livre.

Consumidores: `report-form.ts` (apaga `:16-24` e `:60-69`),
`indicator-form-dialog.ts`, e o novo `AddIndicatorDialog`.

**Spec de paridade (RFC §6):** tabela que constrói **os dois** forms pela factory
e afirma que cada valor-limite é aceito/recusado igual nos dois. A metade pública
já existe (`report-form.spec.ts:53-93`); a metade admin não existe.

### 1.2 — `AddIndicatorDialog` (a entrada única)

Novo `pages/startups/add-indicator-dialog/`. RFC-001 §3.2 especifica a máquina de
estados por completo. Pontos não-negociáveis:

- **Seletor de modo com semântica de rádio** (`role="radiogroup"`, `aria-checked`,
  setas), estilo de chip — modo é exclusivo, então é rádio, não `aria-pressed`.
- **Trocar de modo esconde, não destrói** os controles do outro; o FormGroup
  persiste (critério 6.1.6 — comportamento que deve **sobreviver**, não ser
  reescrito).
- `aria-live="polite"` no painel do modo; foco preso no diálogo; rótulo do botão
  primário acompanha o modo ("Salvar indicador" | "Gerar link").
- Contexto do período derivado dos dados já carregados (`startup-detail` já traz
  indicadores + tokens em `loadAll`; passe por `MAT_DIALOG_DATA`, sem chamada
  nova de rede): avisar "Jul/2026 já possui indicador. Salvar substitui os campos
  preenchidos." e "Já existe um link para este período.".
- Modo link, após gerar: **absorve o `token-panel-dialog` atual** como o painel
  do link (URL como texto, Copiar tolerante a falha, Enviar por WhatsApp).
- Ponto de entrada: substitui os **dois** gatilhos de hoje —
  `startup-detail.html` cabeçalho (`Gerar link`) e barra de seção (`Adicionar
  indicador`). RFC-001 §2 chama essa duplicação de o defeito.

### 1.3 — `indicator-form-dialog` vira só edição/leitura + anotação do fundo

- `indicator-form-dialog` deixa de ser porta de **criação** (isso é o
  `AddIndicatorDialog`); permanece para **editar**.
- **Seção "Anotações do fundo"** própria, separada da zona reportada, na edição
  (hoje `comments` está dentro de "Qualitativos", `indicator-form-dialog.ts:122`)
  e na **vista de leitura** (`app-read-view`). A metade pública (ausência de
  `comments` no form público e nos dois schemas públicos) já está pronta e
  guardada — **não** mexer nela.

### 1.4 — Corrigir dois defeitos reais no caminho de criação

Verificados, sem teste hoje:

- **Campo vazio apaga valor** (`create` como upsert): o form semeia `''`
  (`indicator-form-dialog.ts:65-67`), o controller faz `model_dump` puro
  (`monthly_indicator_controller.py:165`) e o use case só pula `None`
  (`create_monthly_indicator.py:32`). Um textarea limpo **apaga** texto salvo —
  viola PRD §6.1/§8 "vazio não apaga". Normalizar `''`→ausência na borda do
  diálogo/controller.
- **"Indicador criado" mentiroso**: `startup-detail.ts:304` mostra sempre
  "Indicador criado" mesmo quando o POST fez merge sobre período existente. PRD
  §8 pede **aviso prévio** de sobrescrita. Corrigir a mensagem e (com o contexto
  do período já no diálogo) o aviso.

### 1.5 — Consertar os defeitos pequenos do item 5 (dentro da Fase 1)

O painel enviado **conforma ao PRD** (a lista de destinatários é o que o PRD
§9.1 item 4 decidiu para o v1 — **não** mexer no PRD). Divergências são só com a
RFC-001 §3.3, e são de código:

- **Nome acessível**: hoje `token-panel-dialog.html:46` usa "Enviar para {X} no
  WhatsApp"; a RFC-001:221-222 pede "Enviar por WhatsApp para {nome}". Unifique
  (e atualize a RFC se preferir o texto atual — mas escolha um).
- **Mês por extenso na mensagem**: `token-panel-dialog.ts:47` usa `MONTH_LABELS`
  (abreviado, "Jul/2026"); o modelo do fundo que o PRD reproduz verbatim
  (PRD-001:214-221) pede "julho/2026". Precisa de um segundo mapa de rótulo por
  extenso (o título do diálogo fica abreviado de propósito).
- **Prévia do primeiro destinatário**: a prévia da mensagem mostra só o
  primeiro; alinhe ao destinatário efetivamente escolhido.
- **Falha de clipboard (RFC §6)**: `token-panel-dialog.ts:71-75` não trata
  rejeição do `writeText`; a RFC-001:298 lista "falha de clipboard informada"
  como spec própria e §3.2:172-174 exige a cópia tolerante a falha. Adicione o
  tratamento e o spec.

### 1.6 — Mover as edições de skill acopladas (mesma entrega)

O incremento 2 do PRD-002 **navega pela UI que o item 2 remove**. Estas mudam no
mesmo commit da Fase 1, senão a skill passa a apontar para botão inexistente:

- `Server/skills/cobrar-indicadores/SKILL.md:89-99` (Passo 3: "Gerar link" →
  "Gerar link de indicador" → "Gerar", "o diálogo já vem preenchido com o mês
  anterior").
- `Server/skills/operar-portfolioos/references/monitoring.md:77-90` (mesmo
  caminho).
- `Server/tests/unit/test_skills_lint.py:204` afirma o literal "Gerar link de
  indicador".

Reescreva para o fluxo do `AddIndicatorDialog` (ex.: "Adicionar indicador" →
modo "Gerar link para a investida" → "Gerar link").

### 1.7 — Remover o `token-generate-dialog`

A RFC-001 §8 já o declara **extinto**. Depois que o `AddIndicatorDialog` assume,
apague `pages/startups/token-generate-dialog/` e seus specs (RFC §6 lista essa
remoção). O default de mês-anterior que hoje vive no *caller*
(`startup-detail.ts:454`, `:478-484`, com o ramo dezembro→janeiro **sem teste**)
passa para o `AddIndicatorDialog` — e o `indicator-form-dialog` que hoje
hardcoda o mês **corrente** (`:57`) some junto do caminho de criação.

### 1.8 — Reconciliar rótulos e máscara de moeda

Dois pontos que "contrato único" (item 1) força a escolher:

- **Máscara**: o form público usa `appCurrencyInput` (pt-BR mascarado,
  `report-form.html:67,125,162`); o admin usa `type=number` cru
  (`indicator-form-dialog.html:41,67,84`). Um admin digitando `1.500,00` num
  `type=number` esvazia o campo. Unifique na direção da diretiva compartilhada.
- **Rótulos divergentes do mesmo campo**: público "Destaques do mês" /
  "Próximos passos e necessidades" (`report-form.html:185,197`) vs admin
  "Conquistas do mês" / "Desafios do mês" (`indicator-form-dialog.html:93,100`).
  Escolher um par unifica — e obriga atualizar `public-forms.md` ou o spec do
  diálogo (e RFC-002 §5:488). Decida o par e propague.

### 1.9 — Fecho da Fase 1

- Marque os 7 `[ ]` da jornada 6.1 (`docs/prd/001:209-231`) e os 7 da 6.5
  conforme cada um passa.
- Escreva o spec do **fluxo gerar→enviar por papéis e nomes acessíveis**
  (critério 6.5.7 / item 6) — sem seletor de implementação, sem clipboard como
  via única. É o teste que certifica operabilidade por agente.
- Rode os gates de a11y do AGENTS.md no `AddIndicatorDialog` (radiogroup,
  foco, `Escape`, `aria-live`, `prefers-reduced-motion`) e revisão por imagem
  em 375/768/1440 nos dois temas.
- Duas suítes verdes.

---

## Fase 2 — Reconciliação documental (drift sweep)

Depois da Fase 1 (que consolida os nomes finais). Cada item foi verificado com
`file:line`; confirme antes de editar.

### 2.1 — RFC-001

- **§3.1 símbolos**: a RFC prescreve `models/whatsapp-share.ts`
  (`normalizePhoneBR`, `buildWhatsAppShareUrl`, `buildIndicatorInviteMessage`) e
  `models/indicator-form.ts`; o código entregou `models/whatsapp.ts`
  (`normalizeBrazilianPhone`, `buildWhatsAppLink`, `buildIndicatorRequestMessage`,
  `formatBrazilianPhone`, `firstName`). **Decida a direção** (renomear código →
  RFC, ou atualizar RFC → código) e alinhe. A Fase 1 cria `indicator-form.ts`,
  então metade se resolve sozinha.
- **§8 extinção**: `token-generate-dialog` foi declarado extinto mas ainda
  existia e foi remendado; após a Fase 1 estará removido — remova o marcador de
  "pendente". O status por incremento em §8 deve ser **parcial e por
  incremento** (inc. 1 = só guardas de backend; inc. 2 = só o painel, não o
  seletor; inc. 3 = nada — a seção da anotação não tinha sido feita), não "3 done,
  4 partial".
- **§4 headcount**: a tabela de contrato omite o teto de headcount que o backend
  agora impõe (`schemas/monthly_indicator.py:16`). Acrescente a linha.
- **§3.3 destinatário**: atualize para "lista de executivos com telefone" (o que
  foi entregue e o que o PRD decidiu); **não** toque em PRD-001:195-196.
- **Segredo portador**: RFC-001 define o token como "segredo portador" no
  glossário normativo — reconcilie com a decisão de 14/08 (PRD-002 item 6: o link
  **não** é segredo, é capacidade de escrita entregue só ao contato cadastrado).

### 2.2 — PRD-001

- **Segredo portador ×3**: ainda chama o link de segredo em três lugares após a
  reversão de 14/08. Reescreva para "capacidade de escrita, entregue só ao
  cadastro".
- **Data de cabeçalho** (`:7`, 2026-08-11) é anterior ao próprio conteúdo (`:189`,
  `:237` dizem 14/08). Corrija.
- **Status** `Rascunho` → transição (ver §11).

### 2.3 — PRD-002 / RFC-002

- **Página ensina o oposto**: PRD-002/RFC-002 pedem que `/ia` ensine "links de
  indicador são segredos"; a página entregue ensina o contrário (decisão de
  14/08). Reconcilie o texto normativo com a página.
- **"três skills" → cinco** (quatro publicadas): RFC-002 diz "as três skills"
  duas vezes. Atualize.
- **§5 tabela de nomes acessíveis**: incompleta em duas direções. (a) não foi
  estendida para `cobrar-indicadores` (8 nomes), como a própria regra §5:498
  exige; (b) **omite todo o vocabulário do `operar-portfolioos`** — a skill base
  por onde tudo roteia — incluindo os `Ver reunião de {...}`, `Ver executivo
  {...}`, `Ações de {...}` (`monitoring.md:58-71`). Estenda a tabela (§5:482-488)
  para as duas.
- **§5 fragilidade da linha clicável**: a RFC declara a linha de monitoramento
  como "fragilidade real, registrada em §9" (`:490-496`) — mas (i) o código já
  corrigiu (`portfolio.html` com `routerLink` + row-openers) e (ii) a §9 **não
  tem** essa linha (xref pendurada). Reescreva `:490-496` para registrar a
  correção; não mande caçar texto que não existe na §9.
- **§10 roteiro sem item de cobrança**: `:585` afirma que a jornada 6.7 é
  verificada pelo roteiro manual, mas o roteiro (a)–(g) em `:583` não tem
  nenhum item de cobrança. Adicione o item de cobrança ao roteiro **ou** corrija
  a linha de rastreabilidade.
- **§7 ordem de rollout**: passos 1–4 entregues, escritos como futuros e sem
  marcador; o passo 5 (validação com usuário real) nunca foi feito. Anote o
  status por passo — é o **único** registro de que inc. 1 e 2 saíram, então não
  apague sem preservar isso.
- **Datas**: `:7` (2026-08-13) anterior a `:482-483` (14/08); cabeçalho RFC-002
  `:8` idem vs `:606`.

### 2.4 — Documentos de plano e AGENTS.md

- `plano-incremento-1-ia.md`: consumido. Marque como histórico/concluído. E
  corrija `:96` "two product routes" → **três** (`skill_controller.py` guarda
  `:26`, `:39`, `:65`) — senão a próxima sessão que seguir o plano não acha a
  terceira rota.
- `AGENTS.md` *Machine-readable UI*: os dois PRDs citam a seção para regras que
  ela não contém. Ou adicione as regras (padrão de `row-opener`, painel do link,
  nomes acessíveis de ação de linha) ou corrija as citações.
- **Rota individual `GET /api/skills/{name}.zip`**: existe e contradiz RFC-002
  §4. **[DECISÃO ABERTA]** — remover a rota + use case, ou registrar em §11 como
  endpoint retido de propósito. Nenhum cliente a consome.

Fecha quando: `grep` pelos termos obsoletos ("segredo portador", "três skills",
"two product routes", `token-generate`) não retorna nada normativo, e as datas de
cabeçalho batem com o conteúdo.

---

## Fase 3 — Itens travados por governança

**Prepare até a fronteira da decisão; não decida.**

### 3.1 — Publicar `auditoria-qualitativa` — **[TRAVADO — Daniel Braz, open item 4]**

A skill está escrita e completa; a publicação é um flip de flag **mais** uma
cauda que o Opus pode preparar num branch/PR à espera do sim:

- flip `Server/skills/auditoria-qualitativa/.portfolioos.json`
  `"published": true` + remover `blocked_reason` + bump da versão.
- **description sem cláusula de roteamento**: é a única das skills sem "Use
  para…"; adicione (senão o wrapper não roteia para ela).
- **PACK_SKILL.md** sem vocabulário de auditoria nos gatilhos; adicione.
- **~6 docs afirmam a ausência dela** do pacote; atualize quando publicar.
- A política de trânsito de dados é o **entregável do Daniel** (não existe no
  repo hoje) — o `blocked_reason` nomeia "a política"; um "ok" verbal deixaria o
  texto impreciso.

### 3.2 — Incremento 3, `apresentacao-portfolio` — **[TRAVADO — Daniel Braz, open item 5]**

Open item 5 decide só a **distribuição do trio `brq-pptx`**; a skill nova
`apresentacao-portfolio` **entra no catálogo normalmente** (RFC-002 §3.5) — o
trio de marca é que fica fora do repo. O Opus pode escrever a skill (a camada de
conteúdo do fundo: visão executiva de receita/crescimento mês a mês, síntese do
portfólio, prioridades do mês, one-pager qualitativo por investida) enquanto a
decisão de distribuição do trio fica pendente. Precisa de
`plano-incremento-3-ia.md`.

---

## Fase 4 — Escrever PRD-003 e RFC-003

### 4.1 — `docs/prd/003-*.md` (envio autônomo, nível 3)

Espelhe a forma de PRD-001/PRD-002. Cabeçalhos: 1 Resumo; 2 Problema (por que o
nível 2 não fecha: toda execução ainda exige humano); 3 Objetivos/métricas; 4
Escopo + progressão (nível 3 = plataforma envia, sem escolha humana em execução
alguma); 5 Personas (o job é o **primeiro ator sem sessão de administrador**); 6
Jornadas (6.1 detecção por `last_reported`; 6.2 geração em lote; 6.3 disparo; 6.4
falha/reentrega; 6.5 opt-out/parada); 7 Regras transversais; 8 Bordas; 9
Decisões + 9.1 Pendências — **herda obrigatoriamente** PRD-001 pendência 1
(expiração de link deixa de ser opcional) e a **decisão de canal** ainda aberta
(`wa.me` exige confirmação humana → WhatsApp Business API, e-mail, ou "preparado
pelo job, disparado com um clique"). Fecha a numeração cruzada com PRD-001 §9.1
item 1 e PRD-002 §9.1 item 7.

### 4.2 — `docs/rfc/003-conector-mcp.md` (conector MCP com OAuth)

Cabeçalhos espelhando RFC-002 §1..§11: 1 Resumo; 2 Contexto (2.1 Metas, 2.2
Não-metas, 2.3 Linguagem); 3 Arquitetura (3.1 processo — mesmo FastAPI vs
processo irmão **reusando os use cases de `app/application`**, sem segunda
implementação de regra; 3.2 OAuth — authorization code + PKCE, consentimento,
sessões revogáveis por usuário, por que o JWT de login de 60min não serve; 3.3
**catálogo de ferramentas com escopo** — conjunto só-leitura {preparar-agenda,
auditoria-qualitativa} separado do de escrita {granola-reuniao,
cobrar-indicadores} — é o que converte contenção-por-instrução em
contenção-por-capacidade, PRD-002 §7:431-437; 3.4 o que muda nas skills — só a
seção "como alcançar os dados"; 3.5 migração do canal navegador); 4 Contrato MCP
(tools, schemas, mapeamento tool→use case, erros); 5 Testes (fitness de camada,
escopo de token por ferramenta, revogação); 6 Segurança/prompt injection sob
capacidade; 7 Rollout; 8 Alternativas (API key pessoal, reuso do JWT, gateway
externo); 9 Riscos; 10 Rastreabilidade → PRD-002 §4 item 4; 11 Decisões.

---

## Fase 5 — Incremento 4 (conector MCP)

Gated na RFC-003 aprovada. Precisa de `plano-incremento-4-ia.md`. Fundamento
sensato antes da RFC: nenhum — é tudo desenho a fechar na RFC-003 primeiro. Não
comece a implementar OAuth/tools antes de a RFC decidir o split de escopo e o
fluxo de consentimento.

---

## 10. Endurecimento transversal (interleave)

Não bloqueia as fases, mas a estrutura ideal exige. Priorize por "regressão que
sobe verde".

- **Corrida get-then-create → 500.** `CreateMonthlyIndicator` e
  `CreateMonthlyIndicatorToken` são check-then-insert; duas escritas concorrentes
  no mesmo período viram 500 (nenhum `IntegrityError` capturado; `main.py` sem
  handler). **Severidade baixa hoje, ALTA quando o PRD-003 gerar em lote.**
  Correção no repositório: `except IntegrityError` em
  `monthly_indicator_repository.py` — `create` em `:66` (corpo `:67-70`),
  `create_token` em `:192` (corpo `:193-196`). Há precedente no docstring `:10-24`
  (hazard asyncpg-vs-SQLite no mesmo arquivo). **Não invisível a SQLite** — o
  teste que reproduz precisa de Postgres.
- **Determinismo da suíte backend.** Um único `/app/test.db` compartilhado
  (`conftest.py:5,27`, arquivo de 110KB em disco, gitignored `.gitignore:21`),
  sem isolamento por run: dois `pytest` concorrentes/interrompidos se envenenam —
  exatamente o que uma auditoria multi-subagente provoca. Mova o sqlite para fora
  da árvore montada e faça a fixture autouse drop-then-create (`conftest.py:38-45`).
- **`seed_demo.py`.** (i) não semeia executivos → jornada 6.7 critério 5 (startup
  impedida por falta de telefone) sem cenário; (ii) `_remove_scenario_drift`
  (`:127-141`) limpa só indicadores e reuniões — **não** tokens; rodar o roteiro
  §6.7 gera tokens que sobrevivem ao re-seed e envenenam o cenário; (iii) a
  startup semeada nem é "faltante" no período default. Acrescente executivos (com
  e sem telefone), limpe tokens no drift, e garanta um período faltante.
- **Roteiro de aceite RFC-002 §10.** Nunca registrado como rodado; é o segundo
  portão (não-Daniel) da `auditoria-qualitativa` e da cobrança. Depende do
  `seed_demo` acima. Registre a execução (a)–(i) num artefato no repo.
- **Gates de a11y na UI nova.** Nunca rodados em `token-panel-dialog`, coluna
  Telefone, anéis de foco `row-opener`. Rode o script de auditoria do
  `brq-secao` + checagens de teclado/foco/`Escape`/`prefers-reduced-motion`, e
  revisão por imagem em 375/768/1440 nos dois temas.
- **Resíduo de teclado no dealflow.** O card de deal é pointer-only
  (`dealflow.html:39`); o nome da empresa está em `:42` — coloque ali o controle
  `row-opener` (o menu trigger em `:44-45` não é o alvo). Mesma classe do que já
  foi corrigido nas quatro tabelas.
- **Promover `.row-opener` para `styles.scss`** (hoje duplicado em dois `.scss`).
- **Constantes de limite duplicadas** em três arquivos como números mágicos, sem
  guarda cross-linguagem. A factory da Fase 1.1 resolve o lado cliente; considere
  um teste que compare os literais Python e TS.
- **`openai.yaml` aninhado morto**: `Server/skills/operar-portfolioos/agents/
  openai.yaml` viaja no pacote e nunca é lido (a doc já explica em
  `Server/skills/README.md:42-46`; só a **decisão de apagar** está aberta).
  Nenhum teste pega — considere um manifest test contra o `SKILLS_DIR` real.
- **Data de revisão da página `/ia`**: `ai.html:96` mostra 13/08 e o spec
  `ai.spec.ts:238` trava esse valor, mas o pacote mudou (cobrar-indicadores é de
  14/08). É a mitigação que a RFC-002:566 desenhou para "instruções desatualizam"
  — está reportando data mais velha que o conteúdo. Bump + spec.
- **Mapa de título/ordem da `/ia`** (`ai.ts`) exige edição manual a cada skill
  nova — considere derivar do catálogo.
- **Limpeza**: `Server/test.db` e `.pyc` residuais de auditorias antigas fora do
  git.
- **Deploy: verificado limpo** — nenhuma migração, env var ou mudança de compose
  é necessária; `Dockerfile.prod:8` é `COPY . .` e `.gcloudignore` não tem glob de
  dotfile, então `openai.yaml` e `.portfolioos.json` embarcam. (Este item é ✅.)

---

## 11. Decisões que dependem de humano

Consolidadas — o Opus **não** resolve nenhuma:

| # | Decisão | Dono | Trava |
|---|---|---|---|
| PRD-002 open 4 | Política de trânsito de dados (entregável = doc) | Daniel Braz | publicação da `auditoria-qualitativa` |
| PRD-002 open 5 | Distribuição do trio `brq-pptx` | Daniel Braz | só a hospedagem do trio; a skill não |
| PRD-001 open 1 | Expiração de link | Produto/CTO | vira obrigatória no PRD-003 |
| RFC-002 §4 | Rota individual `/skills/{name}.zip`: remover ou reter | Produto | drift documental |
| RFC-001/002 | Aprovação do desenho (status Rascunho/Em revisão → aprovado) | Daniel Braz | end state |
| PRD-003 | Decisão de canal do envio autônomo (`wa.me` vs Business API vs "1 clique") | Produto/CTO | escopo do nível 3 |
| Fase 1.8 | Par de rótulos único (Conquistas/Desafios vs Destaques/Próximos passos) | Produto | reconciliação dos dois forms |

---

## 12. Rastreabilidade — o que fecha cada fase

| Fase | Fecha quando |
|---|---|
| 0 | `git status` limpo; duas suítes verdes num checkout limpo |
| 1 | jornadas 6.1 e 6.5 com todos os `[ ]` marcados; `AddIndicatorDialog` com gates de a11y; `token-generate-dialog` removido; spec do fluxo por papéis passa; suítes verdes |
| 2 | `grep` por termos obsoletos sem retorno normativo; datas de cabeçalho batem; §5/§7/§9/§10 da RFC-002 atualizadas |
| 3 | branches/PRs preparados até a fronteira das decisões do Daniel; nada de flag virado |
| 4 | PRD-003 e RFC-003 escritos, com numeração cruzada fechada; status em revisão |
| 5 | gated — só após RFC-003 aprovada |
| Transversal | corrida coberta por teste (Postgres); §10 registrado; gates de a11y rodados; resíduos limpos |

**Fim do estado ideal:** todos os documentos aprovados; níveis 1–2 entregues e
verificados; nível 3 (PRD-003) e MCP (RFC-003) escritos; `auditoria-qualitativa`
e incremento 3 entregues assim que o Daniel destravar; zero drift entre doc e
código.
