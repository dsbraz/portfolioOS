# Implementation plan — PRD-002 increment 1 (AI in the platform)

- **Branch:** `feat/ia-na-plataforma` (empilhada sobre o redesign e os documentos)
- **Fonte normativa:** [PRD-002](prd/002-ia-na-plataforma.md) · [RFC-002](rfc/002-ia-na-plataforma.md)
- **Última atualização:** 2026-08-13
- **Natureza:** artefato de trabalho — pode ser apagado quando o incremento fechar.

> Os caminhos e modelos abaixo foram **verificados no repositório** em
> 2026-08-13, não lembrados. Cada arquivo novo cita o arquivo existente que
> serve de molde, com a linha **e o símbolo** — porque este plano manda inserir
> linhas em `main.py`, `config.py` e `deploy.sh`, e os números envelhecem
> durante a própria execução. Quando divergirem, o símbolo manda.

## 0. Estado atual da branch

Já feito, e é o passo 1 da RFC §7:

- `skills/` → **`Server/skills/`**, dentro do contexto de build do backend.
  Verificado que chega à imagem: `deploy.sh:52` (`gcloud builds submit ./Server`),
  `Server/cloudbuild.yaml:9` builda com esse contexto, `Dockerfile.prod:8` faz
  `COPY . .` → `/app/skills`. Nenhum dos 10 padrões de `Server/.gcloudignore`
  filtra a pasta.
- Internal skills carry canonical Agent Skills frontmatter (`name` and
  `description` only), backend-only `.portfolioos.json` catalog metadata, and a
  uniform non-negotiable rules section. `operar-portfolioos` is the broad base;
  specialized skills remain independently lintable but are distributed together.

**O que a mudança de pasta deixou quebrado e ainda não foi corrigido** —
`Server/skills/README.md` seguiu junto sem revisão. Ver §9.

**Base de partida, medida em 2026-08-13:** `docker compose exec server pytest`
→ 143 passando; `docker compose exec client npx ng test` → 199 passando em 35
arquivos. As duas suítes verdes antes de qualquer linha deste incremento, que é
a precondição do TDD da §7 — daqui para a frente, teste vermelho é do
incremento.

## 1. Backend do catálogo

Recurso `skill` **sem tabela e sem migração** — lê o filesystem. Segue a cadeia
`controllers → application → domain → repositories`.

A tabela abaixo é o inventário do que existe ao fim da etapa; a **ordem** de
escrita é a da §7, que pareia cada arquivo com o teste que o especifica antes.

| Arquivo | Ação | Molde |
| --- | --- | --- |
| `Server/app/domain/models/skill.py` | criar | `application/portfolio/readmodels.py:8` (`@dataclass(frozen=True)`) — único precedente no backend. **Não** registrar em `domain/models/__init__.py`: aquele arquivo é o registry do SQLAlchemy |
| `Server/app/domain/schemas/skill.py` | criar | `schemas/monthly_indicator.py:105` (schema montado à mão) e `schemas/common.py:9` (`PaginatedResponse`) |
| `Server/app/repositories/skill_repository.py` | criar | `repositories/monthly_indicator_repository.py:27` — diretório injetado no `__init__`, nunca lido de `config` dentro do repo |
| `Server/app/application/skill/__init__.py` | criar | vazio, como os 9 subpacotes existentes de `application/` |
| `Server/app/application/skill/list_skills.py` | criar | `application/startup/list_startups.py:5` |
| `Server/app/application/skill/get_skill_pack.py` | create | returns the complete archive as `bytes`; it must not import `fastapi` or schemas (enforced by the architecture fitness test) |
| `Server/app/controllers/skill_controller.py` | criar | `controllers/monthly_indicator_controller.py:49` — `public_router` sem prefixo próprio |
| `Server/app/config.py` | editar | `skills_dir: str = "/app/skills"` e `skills_public: bool = True` no `Settings` — **com default explícito**, senão dev e prod divergem em silêncio |
| `Server/app/controllers/auth_dependency.py` | editar | extrair o corpo de `get_current_user:16` para um `_resolve_user(token, session)`; ver "Mecânica do `skills_access`" abaixo |
| `Server/app/controllers/dependencies.py` | editar | provider do repositório **sem sessão**, no molde de `_get_password_hasher:85`; e `skills_access` (mecânica abaixo — **não** no molde de `verify_startup_exists:94`) |
| `Server/app/main.py` | editar | incluir no bloco **público** (`main.py:50`, comentário `# Public routes`), nunca na lista `protected:57`; fail-fast do `SKILLS_DIR` no `lifespan:29` |

### Campos do modelo de domínio

`name`, `description`, `version`, `writes`, `reads_external`, `published`,
`blocked_reason`, `files`. `name` and `description` come from canonical
`SKILL.md` frontmatter; `version`, `writes`, `reads_external`, `published`, and
the conditional `blocked_reason` come from `.portfolioos.json`. The API shape
does not expose that source split.
Sem ele o card bloqueado não tem motivo para exibir e a condicionante de
lançamento da RFC §7 falha. Ver §10.

### Decisões já fechadas na RFC — não se rediscutem ao codar

- **Discover internal skills from known directories**, never from a caller
  path. A directory participates only when it contains `SKILL.md`. The
  qualificador não é teórico: `Server/skills/README.md` está no topo do
  `SKILLS_DIR` hoje, e um `iterdir()` ingênuo o transforma em entrada lixo do
  índice ou estoura o parser.
- **Varredura recursiva** (o formato prevê `references/`, `scripts/`,
  `assets/`), ignorando ocultos e `__pycache__`.
- **The ZIP has one `portfolioos/` root.** It contains a root `SKILL.md` upload
  wrapper, `README.md`, `.codex-plugin/plugin.json`,
  `.claude-plugin/plugin.json`, and published skills under `skills/<name>/`.
- **`"published": false`** in `.portfolioos.json` stays out of the complete ZIP and **present in the catalog** with
  `blocked_reason` e sem `files`.
- **Both parsers use the stdlib.** Canonical frontmatter uses `split("---")`;
  the hidden catalog sidecar uses `json`. No YAML dependency is added, and
  `Server/requirements.txt` is not touched in this increment.

### Mecânica do `skills_access`

A RFC §4 é normativa aqui e o plano anterior transportava só o nome. O
contrato completo:

- lida **por requisição**, nunca por inclusão condicional de router — o
  `include_router(..., dependencies=...)` é decidido no import e não alterna em
  runtime, o que transformaria o kill switch em placebo até o próximo deploy;
- applied to the **two product routes**, `/api/skills` and `/api/skills.zip`;
- com `SKILLS_PUBLIC=false`, exige sessão válida e devolve **401** sem ela.

O molde óbvio não serve: `verify_startup_exists` (`dependencies.py:94`) levanta
**404** e depende de sessão de banco. E `security = HTTPBearer()`
(`auth_dependency.py:13`) tem `auto_error=True`, então `Depends(get_current_user)`
sempre exige o header — não há como compor condicionalmente.

Caminho escolhido, que evita tanto a duplicação quanto o refactor de todas as
rotas protegidas: extrair o corpo de `get_current_user` para
`_resolve_user(token, session) -> User`, deixando `get_current_user` como
invólucro fino (assinatura inalterada, nenhuma rota protegida muda), e escrever
`skills_access` sobre um `HTTPBearer(auto_error=False)` próprio + `_resolve_user`.
Assim a decodificação do JWT vive num lugar só, como manda o AGENTS.md.

The archive response uses `media_type="application/zip"` and
`Content-Disposition: attachment; filename="portfolioos.zip"`.

## 2. Testes do backend

| Arquivo | Cobre | Molde |
| --- | --- | --- |
| `tests/integration/test_skill_api.py` | ver a lista de asserções abaixo | `tests/integration/test_user_invite_api.py:12` (`@pytest.mark.asyncio` explícito, fixture `anon_client`); para o ramo autenticado, a fixture `client` do conftest |
| `tests/unit/test_skill_repository.py` | complete-package membership, root layout, recursive files, and blocked-skill exclusion | `tests/unit/test_get_portfolio_summary.py:12` (`@pytest.fixture`); use `tmp_path` for a controlled source tree |
| `tests/unit/test_skills_lint.py` | ver "Lint" abaixo | — |
| `Server/tests/conftest.py` | editar: `SKILLS_DIR` apontando para `Server/skills/` **antes** do `from app.config import settings` | linhas 4-5 (`os.environ.setdefault`) |

### Asserções do teste de integração

1. **The catalog lists every recognized internal skill**, including
   `operar-portfolioos`; only published records include `files`. Derive the
   expected set from `SKILLS_DIR`, never from a numeric literal.
2. Skill bloqueada aparece com `published: false` + `blocked_reason` e **sem**
   `files`; skill publicada vem **sem** `blocked_reason` (a RFC §4 fixa a forma
   nas duas direções — decidir se é `exclude_none` ou omissão no schema, e
   testar, senão sai `"blocked_reason": null` em toda skill publicada).
3. Forma da resposta: `{ items: [...], total }`. O `total` é do contrato e
   precisa de asserção — o consumidor não é só o Angular, é um agente lendo JSON.
4. Complete ZIP: one `portfolioos/` root; exact package-level wrapper, README,
   and both manifests; recursive published source files under
   `portfolioos/skills/<name>/`; no hidden files or `__pycache__`.
5. The archive includes `operar-portfolioos` and every published specialized
   skill, and excludes every blocked skill. Assert specifically that
   `auditoria-qualitativa` remains in the catalog with its reason but has no ZIP
   entry. The response filename is `portfolioos.zip`.
6. **`SKILLS_PUBLIC` in both states, six assertions**: open serves catalog and
   complete archive without a session; closed returns 401 for both without a session **and 200 for both with a
   sessão válida**. Sem o ramo autenticado, uma implementação que negue acesso a
   todo mundo passa verde e o kill switch vira botão de desligar o recurso.
   Como alternar: `settings` é singleton instanciado no import
   (`config.py:18`), então mexer em `os.environ` dentro do teste não surte
   efeito — `monkeypatch.setattr(settings, "skills_public", False)`, o que só
   funciona porque a dependência lê o atributo por requisição (§1).

### Lint das skills

Duas verificações, ambas estruturais (o lint sabe dizer se a frase está lá, não
se a skill é boa — o comportamento é a §8):

1. **Metadata contracts**: `SKILL.md` frontmatter contains exactly `name` and
   `description`, with `name` matching the directory and a non-empty
   description. `.portfolioos.json` contains a date-formatted `version` and
   JSON booleans for `writes`, `reads_external`, and `published`;
   `blocked_reason` is required when—and only when—`published` is false. The
   hidden sidecar must never appear in `files` or either ZIP.
2. **Anchor phrases inside `## Regras (inegociáveis)`.** Scope the search to
   that section, not the entire file. Rollout step 2 standardizes the heading
   across all internal skills to give the lint a fixed point; scanning the full
   file could accept a phrase that appears only in an example.
   Fixar as strings buscadas, para o lint não ficar sujeito a paráfrase:
   `writes: true` exige prévia confirmada e "nunca peça nem digite senha";
   `reads_external: true` exige "dado, nunca instrução".
3. **Granola source routing.** The lint fixes the decision order and safety
   anchors: inspect/probe Granola tools first; use `get_account_info`,
   `list_meetings`, `get_meetings`, and `get_meeting_transcript` when
   available as unequivocally read-only operations; otherwise disclose the
   data transit and request an authorized exact-host
   `https://notes.granola.ai/...` link. Reject misleading URLs, nonstandard
   ports, and cross-host redirects; never change sharing permissions or echo
   the link. Full-transcript coverage requires every page/cursor and an explicit
   completeness signal. Copied text remains the last resort.

### Por que o conftest não é opcional

Não é que a coleta quebre — **ela não quebra**. O fail-fast mora no `lifespan`
(`main.py:29`), e o transporte do conftest (`ASGITransport(app=app)`,
`conftest.py:76` e `:96`) **não dispara eventos de lifespan**. Sem a linha no
conftest, o repositório resolve contra `/app/skills`, que não existe no host, e
os testes de catálogo passariam a exercitar um diretório vazio — falha
silenciosa, pior que a quebra.

O corolário: **o fail-fast fica sem cobertura nenhuma**, e sua única validação
acaba sendo o deploy em produção. Ver §5, onde ele vira passo de verificação
manual da imagem.

## 3. Página `/ia`

**Decisão de nomenclatura (fechada, não sugerida):** rota `/ia` (é UI, e UI é
PT-BR), pasta e classe em EN-US — `pages/ai/`, `class Ai`. Não há exceção a
registrar: o espelhamento pasta↔rota já não é universal
(`monthly-indicator/:token` → `pages/report/`, `app.routes.ts:45`).

| Arquivo | Ação | Molde |
| --- | --- | --- |
| `Client/src/app/models/skill.model.ts` | criar | `models/startup.model.ts` |
| `Client/src/app/services/skill.service.ts` | criar | `services/startup.service.ts:12` — URL **relativa** (`/api/skills`) |
| `Client/src/app/pages/ai/ai.{ts,html,scss}` | criar | `pages/portfolio/*` (três ramos de estado, `aria-busy` no container) e `pages/users/users.scss:11` (bloco `.page-head`, que **não** é global) |
| `Client/src/app/app.routes.ts` | editar | copiar o bloco de `users:34` — `canActivate: [authGuard]`, **sem** `data: { public: true }` |
| `Client/src/app/app.html` | editar | novo `<li>` copiando o item Usuários (`app.html:52`), com `ariaCurrentWhenActive="page"` |
| `Client/src/app/pages/ai/ai.spec.ts` | criar | `pages/portfolio/portfolio.spec.ts:13` (`describe`) |
| `Client/src/app/services/skill.service.spec.ts` | criar | `services/startup.service.spec.ts:8` (`describe`) e `:12` (`beforeEach` com `provideHttpClient() + provideHttpClientTesting()`); `httpMock.verify()` no `afterEach`, como em `:20` |

### Page interaction contract

Product copy remains **in the Angular template**, not rendered Markdown. The
primary experience is install-once and capability-complete:

1. **One package CTA.** Render one primary button with the accessible label
   `Baixar pacote de skills portfolioOS`. It calls
   `SkillService.downloadPack()` for `/api/skills.zip` and saves
   `portfolioos.zip`; the auth interceptor therefore preserves the flow when
   `SKILLS_PUBLIC=false`.
2. **Always-visible installation guidance.** Show short ChatGPT and Claude
   instructions together. Do not gate either path behind a selector, tab,
   accordion, preference, completed step, or stored state. Describe the
   objective (upload/install the package), not a brittle menu path.
3. **Natural-language start.** Show several short PT-BR examples of outcomes
   that the installed package can handle. Do not expose internal slugs, canned
   prompts, or a copy button. The runtime discovers the base or specialized
   internal skill from intent.
4. **Explanatory catalog.** Render API metadata as a capability overview, not
   as selectable tasks. Published capabilities describe what is already inside
   `portfolioos.zip`. `published: false` entries render in `Ainda não
   disponíveis` with textual status and `blocked_reason`; they have no action
   and contribute no files to the archive.
5. **Visible session and safety notes.** Explain that Claude can use the current
   browser session while ChatGPT agent mode may open a separate browser where
   the user signs in directly. Always state `Nunca digite sua senha no chat`,
   `Não compartilhe links de indicadores`, and that every write requires a
   preview and explicit confirmation.
6. **Manual update.** Tell the user to download the complete package again and
   replace/reinstall it. Never ask them to compare internal skill versions.

The archive's root wrapper covers single-upload runtimes; its plugin manifests
cover compatible plugin runtimes. The page makes no marketplace-publication or
organization-wide-deployment promise.

### Data and action rules

- The sole download is an authenticated `HttpClient` blob request to
  `/api/skills.zip` through `SkillService`, followed by a browser save as
  `portfolioos.zip`.
- Catalog data never determines a download URL, prompt, copy action, or
  per-capability install control.
- Blocked state is derived from `published: false` + `blocked_reason`, never a
  hard-coded template list. It remains visible for auditability.

### Blocos compartilhados a reusar (não inventar)

`styles.scss` já tem `.pill` (`:1221`, com `--good/--warn/--danger/--info/--neutral`),
`.tag` (`:1283`), `.section-title` (`:566`), `.page-status` (`:583`) e
`.visually-hidden` (`:595`). O estado bloqueado é `.pill` — status estático
pareado com rótulo —, **nunca** um estilo novo. Cards em `--radius-md`. O
`blocked_reason` é **texto**, não cor. Nenhum hex/rgb em SCSS ou TypeScript.

### Spec coverage

Green specs require behavioral assertions, not only component creation:

- exactly one download button requests `/api/skills.zip` and names the saved
  file `portfolioos.zip`, including the success and failure states;
- ChatGPT and Claude instructions are both visible, with no tool or skill
  selector, preference, default, or persistence;
- natural examples render with no internal slug or prompt-copy action;
- contextual safety includes credentials, secret links, and
  preview/confirmation before every write;
- catalog records are explanatory; blocked state comes **from API data**, shows
  its textual reason, and has no action; switching to `published: true` changes
  package membership without requiring an item-level UI control;
- loading / content / error branches remain explicit;
- `/ia` remains protected by the guard.

## 4. Specs do contrato de navegação das skills

This section locks the accessible names used by the browser workflows, which a
previous plan reduced to a prose warning ("do not rename"). Prose is not a
mechanism: the next redesign could silently break the installed package. These
specs implement the RFC §9 mitigation for UI drift; the PRD-001 operability
test does not cover these screens.

Os cinco alvos **já existem** — são edições, não criações:

| Tela (RFC §5) | Arquivo | Nomes a travar | Cobertura hoje |
| --- | --- | --- | --- |
| Navegação | `Client/src/app/app.spec.ts` | "Monitoramento" | nenhuma |
| Monitoramento | `pages/portfolio/portfolio.spec.ts` | colunas Startup, Status, Receita, Caixa, EBITDA/Burn, Headcount; notas "Último: …" e "Nunca reportou" | só "Nunca reportou" (`:371`) |
| Detalhe da startup | `pages/startups/startup-detail/startup-detail.spec.ts` | abas "Indicadores Mensais", "Reuniões de Conselho", "Executivos"; botões "Adicionar reunião" e "Adicionar indicador"; cartões Receita Total, Total da Participação, Saldo em Caixa, EBITDA/Burn, Headcount | nenhuma |
| Diálogo de reunião | `pages/startups/meeting-form-dialog/meeting-form-dialog.spec.ts` | título "Nova Reunião de Conselho"; rótulos Data, Participantes, Resumo, Pontos de Atenção, Próximos passos; botão "Adicionar" | nenhuma |
| Vista de leitura | `pages/startups/indicator-form-dialog/indicator-form-dialog.spec.ts` | rótulos Conquistas do mês, Desafios do mês, Comentários; botão "Fechar" | só "Conquistas do mês" (`:63`) |

Regra de processo que vem junto (RFC §5): **skill nova obriga a estender esta
lista**. Sem ela o contrato nasce e congela — os incrementos 2 e 3 trazem nomes
acessíveis novos que ninguém vai travar.

## 5. Deploy e configuração

| Arquivo | Mudança |
| --- | --- |
| `deploy.sh` | duas linhas dentro do heredoc `ENV_VARS_FILE` (`:61-66`), na forma exata de `ACCESS_TOKEN_EXPIRE_MINUTES:64`: `SKILLS_DIR: "${SKILLS_DIR:-/app/skills}"` e `SKILLS_PUBLIC: "${SKILLS_PUBLIC:-true}"` — **com aspas**, porque `--env-vars-file` rejeita booleano YAML |
| `docker-compose.yml` | `SKILLS_PUBLIC: ${SKILLS_PUBLIC:-true}` no `environment:` do serviço `server` — **com o default**, na forma de `ACCESS_TOKEN_EXPIRE_MINUTES:27`, nunca na de `DATABASE_URL:25`. O `SKILLS_DIR` já funciona pelo mount |
| `.env.example` | `SKILLS_PUBLIC=true` — é o arquivo do fluxo de dev (`cp .env.example .env` no README), e o plano anterior não o citava |
| `.env.production.example` | as duas variáveis comentadas com default explícito |
| `DEPLOY.md` | duas linhas na tabela de variáveis + o procedimento de flip emergencial do `SKILLS_PUBLIC` |

**Por que a forma no compose importa:** `${SKILLS_PUBLIC}` sem default injeta
string vazia quando a variável não existe no `.env` de alguém; `Settings()` roda
no import (`config.py:18`) e levanta `ValidationError`. É a armadilha 2 desta
mesma página, só que em desenvolvimento — o container `server` entra em crash
loop para todo mundo que der pull na branch.

### Verificação, que o plano anterior não agendava

1. **Antes do deploy**, inspecionar a imagem construída:
   `docker run --rm <image> ls -R /app/skills`. Sem isso a armadilha 3 se
   realiza em silêncio.
2. **After deploy**, smoke test `GET /api/skills` and download
   `$BACKEND_URL/api/skills.zip` as `portfolioos.zip`. Inspect the archive for
   the root wrapper, both manifests, `skills/operar-portfolioos/`, all published
   specialized skills, and the absence of `auditoria-qualitativa`.
3. **Caminho de volta.** A RFC escolheu falha alta no startup: se o diretório
   não existir, **não é o catálogo que fica vazio, é o processo que não sobe** —
   o startup probe do Cloud Run (`deploy.sh:80`, `/api/health/ready`) nunca passa
   e a API inteira cai. A resposta é rollback da revisão no Cloud Run, e isso
   precisa estar no `DEPLOY.md` junto do procedimento do `SKILLS_PUBLIC`.

## 6. Armadilhas verificadas (não hipotéticas)

1. **`--env-vars-file` substitui o conjunto inteiro.** O repositório já
   demonstra: `CORS_ORIGINS` não está no heredoc e por isso é reaplicado com
   `--update-env-vars` no passo 7 do `deploy.sh`. Um flip emergencial de
   `SKILLS_PUBLIC` feito fora do heredoc é apagado no deploy seguinte.
2. **Boolean inválido derruba o serviço.** `Settings()` roda no import
   (`config.py:18`); `"nao"` ou `"TRUE "` levantam `ValidationError`, o
   gunicorn não sobe, e a falha é total — não degradação.
3. **`Server/.gcloudignore:9` ignora `tests/` em qualquer profundidade.** Uma
   skill futura com `skills/<nome>/tests/` some da imagem em silêncio: o índice
   a lista (o `SKILL.md` chega) e o zip sai incompleto.
4. **`WORKDIR /app` é hardcoded** (`Dockerfile.prod:3`) e o default
   `/app/skills` depende disso por convenção, não por contrato.
5. **`.zip` não casa a regex de estáticos do nginx** (`Client/nginx.conf:10`),
   então cai na `location /api/` — o comportamento desejado. Verificar se
   alguém mexer nessa regex.
6. **Não usar `pyyaml`.** Ele não está no `requirements.txt`, e a RFC §2 fechou
   o parser em `split("---")`. Acrescentá-lo exigiria
   `docker compose build server` (o container de dev não reinstala dependências
   no reload) e mudaria o tipo de `version` e dos booleanos antes do lint ver.
7. **`.page-head` não é global**: cada página repete o bloco. Copiar de
   `users.scss:11`, não importar de outra página. (A linha 4 do arquivo é
   `.users-page`, o wrapper — não é o bloco procurado.)
8. **Do not introduce tool or skill selection.** The page has one package CTA;
   both installation paths stay visible; catalog entries are explanatory and
   have no download, install, prompt, or copy action. If a catalog list becomes
   scrollable, its focus ring must be inset because overflow clips an outward
   outline on all four sides.
9. **Não renomear itens de menu existentes**: "Monitoramento" é nome acessível
   travado pela RFC §5 — e a partir da §4 deste plano, por spec.

## 7. Ordem de implementação e o que fecha cada etapa

AGENTS.md requires TDD by default, so work proceeds in red→green pairs. The
package-manifest test comes first: written after implementation, it would only
confirm the current archive instead of specifying its single-root, dual-mode,
published-only contract.

| Etapa | Pares | Fecha quando |
| --- | --- | --- |
| 1. Repository | `test_skill_repository.py` → `skill_repository.py` | complete archive layout, membership, recursive inclusion, and blocked exclusion are green |
| 2. Skill lint | `test_skills_lint.py` → frontmatter + sidecar parsers | all recognized skills pass; non-standard frontmatter and a seeded blocked skill without `blocked_reason` fail |
| 3. Use cases + routes | `test_skill_api.py` → model, schema, use cases, controller, `skills_access` | catalog plus `/api/skills.zip` assertions in §2, including both `SKILLS_PUBLIC` states |
| 4. Deploy/config | — | `docker compose up` sobe com as variáveis; imagem inspecionada; `deploy.sh` revisado; rollback documentado |
| 5. Serviço + modelo no front | `skill.service.spec.ts` → `skill.service.ts` | spec verde |
| 6. `/ia` page | `ai.spec.ts` → `ai.{ts,html,scss}` | the install-once behaviors in §3 are green; gates below pass |
| 7. Contrato de navegação | 5 specs da §4 | verdes, com os nomes das cinco telas travados |
| 8. Verificação manual das skills | roteiro da §8 | os cinco itens (a)–(e) executados, com dono |
| 9. Non-technical user validation | PRD criterion 6.1 | one person downloads and installs `portfolioos.zip` once, then starts two distinct workflows naturally without naming a skill |

### Gates (AGENTS.md), na etapa 6

Valem para a página **e** para o item novo da sidebar, que é mudança visual e
não cai no escopo "página":

1. **Accessibility** — run the `brq-secao` audit with zero `fail`, then verify
   keyboard operation, visible focus, the single button's accessible name and
   preparation state, and
   `prefers-reduced-motion`. There is no tool- or skill-selection state. Heading
   hierarchy and DOM order follow download → both installation paths → contextual
   safety and help → natural examples → catalog → blocked capabilities; blocked
   state and reason remain textual.
2. **Craft** — revisão por imagem em 375 / 768 / 1440, nos dois temas.

Duas ressalvas do AGENTS.md que precisam estar à mão na hora: **compositar o
alpha** ao medir contraste (o script do `brq-secao` tem esse bug, e o card
bloqueado usa tinta), e as duas armadilhas de medição — aba sem foco não
completa a animação, e `resize_window` não muda `innerWidth` (use um `<iframe>`
same-origin do tamanho alvo).

## 8. Verificação de comportamento das skills

Seção nova, e a omissão mais grave do plano anterior. O lint é **declaradamente
estrutural** (RFC §3.4: "ele não verifica comportamento"), e a contenção por
capacidade só chega no incremento 4. Sem esta etapa, o incremento 1 pode ser
lançado com o guardrail "zero escritas sem confirmação" apenas **declarado** na
skill e nunca observado, e com a defesa anti-injeção indicada por
`reads_external: true` nunca exercitada — sendo que a RFC §9 registra injeção no
qualitativo como risco cuja mitigação **inclui este roteiro**.

**Dono: quem publica a skill no catálogo.** Nenhum lint verifica isto.

### Pré-requisito: o cenário de referência

O PRD §6.5 define o cenário como **artefato, não ideia**: uma startup de
demonstração semeada com três achados conhecidos — (a) contradição texto×número
("mês excelente" com receita caindo), (b) o mesmo próximo passo repetido em duas
reuniões consecutivas, (c) três meses sem qualquer preenchimento qualitativo.
Vive no seed de desenvolvimento e é mantido por quem publica a skill.

**Implementado em `Server/scripts/seed_demo.py`.** O comando idempotente restaura
o conjunto exato de indicadores e reuniões da startup de demonstração, remove
o drift criado pelo próprio roteiro manual e só executa com
`ENVIRONMENT=development` ou `ENVIRONMENT=local` explícito.

**Decisão aplicada — o mecanismo.** As três opções não são equivalentes:

| Opção | Por que serve / não serve |
| --- | --- |
| Migração Alembic de dados | **não** — mistura dado de demonstração com evolução de schema, e roda em produção junto com as outras |
| Fixture de pytest | **não** — insuficiente sozinha: o roteiro (a)–(e) é executado por uma pessoa com um agente operando o **navegador** contra a aplicação de pé, não pela suíte |
| Script idempotente (`Server/scripts/seed_demo.py`, via `docker compose exec server python -m scripts.seed_demo`) | **sim** — é o único que atende ao uso real |

O script foi adotado. `README.md` registra o comando de desenvolvimento
`docker compose exec server python -m scripts.seed_demo`.

### O roteiro (RFC §10)

| # | Verificação | Critério do PRD |
| --- | --- | --- |
| a | Granola MCP utilizável → a skill confirma conta/workspace e obtém a conversa sem pedir link | 6.4 |
| b | Granola MCP indisponível ou sem acesso → a skill pede o link, não altera compartilhamento e declara a cobertura visível | 6.4 |
| c | MCP oferece somente escrita, ou resposta truncada/paginada → nenhuma escrita no Granola; cobertura completa só após todas as páginas | 6.4 |
| d | URL enganosa ou redirect cross-host → não abre/continua; link válido nunca aparece na prévia ou registro | 6.4 |
| e | transcrição-armadilha com instrução embutida → nenhum efeito além do registro proposto, e o desvio é relatado | 6.4 |
| f | startup semeada com contradição, compromisso repetido e silêncio → os três achados aparecem, cada um com origem | 6.5 |
| g | a prévia confere com o registro salvo | 6.4 |
| h | campo qualitativo semeado com instrução embutida → a varredura não muda e a instrução vira achado de segurança | 6.5 |
| i | `preparar-agenda` sobre a mesma startup semeada → as perguntas citam os fatos plantados | 6.3 |

### Rastreabilidade dos critérios do incremento 1

| Critério | Verificado por |
| --- | --- |
| 6.1 — install-once page flow is completable by a non-technical user | §3 content + §3 specs + step 9 (real user) |
| 6.2 — complete package exposes several capabilities without individual selection | catalog and complete-ZIP tests from §2 + single-link specs + two-request user validation |
| 6.3 / 6.4 / 6.5 — **estrutura** das skills | lint da §2 + specs de nomes acessíveis da §4 |
| 6.3 / 6.4 / 6.5 — **comportamento** das skills | roteiro (a)–(e) desta seção |
| Guardrail "zero escritas sem confirmação" | lint garante que a skill **declara**; que o agente **cumpra** só o roteiro observa |

## 9. Documentação a atualizar

Nenhum destes está em CI (não existe `.github/`), então nada detecta a
defasagem.

| Arquivo | O que corrigir |
| --- | --- |
| `Server/skills/README.md` | dois **links mortos** deixados pela mudança da §0: `:7` e `:20` apontam `../docs/prd/...`, que a partir de `Server/skills/` resolve para `Server/docs/` — o certo é `../../docs/prd/...`. E `:21` afirma que a skill bloqueada fica **"fora do índice"**, o oposto do desenho da RFC §3.2 — ela aparece no índice, com o motivo. A seção "Como usar hoje (antes da página de distribuição)" (`:38`) fica obsoleta quando `/ia` entrar no ar, assim como a frase de `:47` |
| `README.md` (raiz) | a árvore de páginas (`:60-66`) não tem a página nova; "Rotas publicas: `/health`, `/health/ready`, `/auth/login`, `/monthly-indicator/{token}`" (`:161`) passa a ser **falsa** com as duas rotas novas, e a tabela de endpoints (`:164`) não as lista; a tabela de variáveis (`:218`) não tem `SKILLS_DIR` nem `SKILLS_PUBLIC` |

## 10. Divergências a corrigir na RFC-002

Encontradas ao confrontar plano e RFC. Não bloqueiam a implementação, mas
deixam RFC e código divergentes:

- **`skills_repository.py` (plural)** em RFC §3.2, três vezes. A convenção real
  é singular (`startup_repository.py`, `user_repository.py`,
  `monthly_indicator_repository.py`). O plano usa singular; a RFC é que está
  fora do padrão da casa.
- **A lista de campos do dataclass (RFC §3.2) omite `blocked_reason`**, que a
  própria RFC exige em §3.2, §3.3 e §4. Ver §1.
- **"catálogo lista exatamente as skills publicadas" (RFC:358)** contradiz
  RFC:186-193 e RFC:361, que mandam a bloqueada aparecer no índice. É a mesma
  ambiguidade que estava na tabela de testes deste plano.
- **PRD-002 §10 (`:410-411`) e RFC-002 §10 (`:10`, `:23`)** ainda apontam
  `skills/` na raiz, caminho que a §0 já mudou.
- A RFC **não menciona schema** entre as camadas; o AGENTS.md exige que
  validação e serialização vivam nos controllers, então o
  `domain/schemas/skill.py` do plano é acréscimo legítimo, não divergência.
- **Invariante de vendor** (RFC §5): condicional ao incremento 3 e à pendência 5
  do PRD, fora deste escopo. Registrado aqui só para que, se alguém adotar
  `SKILLS_VENDOR_DIR` depois, lembre que a invariante de não-publicação é
  obrigatória e testável — sem ela o mount publica o template proprietário de
  7,8 MB para qualquer anônimo.

## 11. Decisões que ainda dependem do Daniel

Antes das pendências, um fato de estado: **as duas fontes normativas ainda não
estão aprovadas.** O PRD-002 está como *Rascunho*; a RFC-002 está *Em revisão* e
sua última linha é `Aprovação do desenho | pendente — Daniel Braz`. Para as
etapas 1 a 5 o risco é baixo — as decisões técnicas estão marcadas "fechada
nesta RFC" e são internamente consistentes. Para a etapa 6 é diferente: o
conteúdo da página é exatamente o que as pendências abaixo moldam.

None prevents implementation from starting. However, **open item 4 blocks the
release** of `auditoria-qualitativa`. It remains visible in the explanatory
catalog with its reason and contributes no files to the complete archive.

**Decision recorded on 2026-08-13:** one `portfolioos.zip` supports ChatGPT and
Claude. Users install it once; the root wrapper or compatible plugin manifest
discovers the internal skills. There is no tool or skill choice, no individual
download, and no item-level prompt/copy flow. The package manifests do not
promise marketplace publication.

The three decision items that still touch this implementation:

- **Open item 1 — AI-tool plan (individual vs. team):** may affect optional
  organization deployment guidance. Personal upload of the complete archive is
  the v1 baseline; no marketplace or centralized-deployment promise is made.
- **Resolved item 2 — Granola conversation source:** `granola-reuniao` first
  inspects and probes the Granola MCP tools. When usable, it confirms the
  account/workspace and fetches the exact meeting there. Otherwise it requests
  a user-provided `https://notes.granola.ai/...` link; copied transcript text is
  a last resort. This branching is automatic and does not change package
  installation or ask the user to choose a source.
- **Pendência 4 — trânsito de dados**: mantém a `auditoria-qualitativa` com
  `"published": false` em `.portfolioos.json`. O mecanismo já existe; liberar
  é editar o sidecar e remover `blocked_reason`.
