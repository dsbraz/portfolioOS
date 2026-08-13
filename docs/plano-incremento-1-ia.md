# Plano de implementação — Incremento 1 do PRD-002 (IA na plataforma)

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
- As três skills carregam o contrato de frontmatter e o cabeçalho
  `## Regras (inegociáveis)` uniforme, que o lint usa como ponto fixo.

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
| `Server/app/application/skill/get_skill_package.py` | criar | `application/startup/get_startup.py:7` — devolve `bytes \| None`; **proibido** importar `fastapi` ou schemas (fitness function em `tests/architecture/`) |
| `Server/app/controllers/skill_controller.py` | criar | `controllers/monthly_indicator_controller.py:49` — `public_router` sem prefixo próprio |
| `Server/app/config.py` | editar | `skills_dir: str = "/app/skills"` e `skills_public: bool = True` no `Settings` — **com default explícito**, senão dev e prod divergem em silêncio |
| `Server/app/controllers/auth_dependency.py` | editar | extrair o corpo de `get_current_user:16` para um `_resolve_user(token, session)`; ver "Mecânica do `skills_access`" abaixo |
| `Server/app/controllers/dependencies.py` | editar | provider do repositório **sem sessão**, no molde de `_get_password_hasher:85`; e `skills_access` (mecânica abaixo — **não** no molde de `verify_startup_exists:94`) |
| `Server/app/main.py` | editar | incluir no bloco **público** (`main.py:50`, comentário `# Public routes`), nunca na lista `protected:57`; fail-fast do `SKILLS_DIR` no `lifespan:29` |

### Campos do modelo de domínio

`name`, `description`, `version`, `writes`, `reads_external`, `published`,
`blocked_reason`, `files`. **A lista da RFC §3.2 omite `blocked_reason`** — é
erro dela: §3.2 (contrato do frontmatter), §3.3 (card bloqueado) e §4 (resposta
do índice) o exigem, e a `auditoria-qualitativa` já o carrega no frontmatter.
Sem ele o card bloqueado não tem motivo para exibir e a condicionante de
lançamento da RFC §7 falha. Ver §10.

### Decisões já fechadas na RFC — não se rediscutem ao codar

- **Resolução por lista de pastas conhecidas**, nunca concatenando o parâmetro
  num caminho. Entra na lista quem é **diretório E contém `SKILL.md`**. O
  qualificador não é teórico: `Server/skills/README.md` está no topo do
  `SKILLS_DIR` hoje, e um `iterdir()` ingênuo o transforma em entrada lixo do
  índice ou estoura o parser.
- **Varredura recursiva** (o formato prevê `references/`, `scripts/`,
  `assets/`), ignorando ocultos e `__pycache__`.
- **Entradas do zip prefixadas** com o nome da skill.
- **`published: false`** fica fora do zip e **presente no índice** com
  `blocked_reason` e sem `files`.
- **Parser de frontmatter é `split("---")` da stdlib.** A RFC §2 fechou isso, e
  a escolha não é cosmética: com PyYAML, `version: 2026-08-11` chega como
  `datetime.date` e `published: no` como `bool`, o que muda o significado do
  lint da §2. `Server/requirements.txt` **não é tocado** neste incremento.

### Mecânica do `skills_access`

A RFC §4 é normativa aqui e o plano anterior transportava só o nome. O
contrato completo:

- lida **por requisição**, nunca por inclusão condicional de router — o
  `include_router(..., dependencies=...)` é decidido no import e não alterna em
  runtime, o que transformaria o kill switch em placebo até o próximo deploy;
- aplicada às **duas** rotas;
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

**Primeiro uso de `fastapi.responses` no projeto** (conferido em 2026-08-13:
nenhum controller retorna `Response` cru). O zip sai com
`media_type="application/zip"` e `Content-Disposition: attachment`.

## 2. Testes do backend

| Arquivo | Cobre | Molde |
| --- | --- | --- |
| `tests/integration/test_skill_api.py` | ver a lista de asserções abaixo | `tests/integration/test_user_invite_api.py:12` (`@pytest.mark.asyncio` explícito, fixture `anon_client`); para o ramo autenticado, a fixture `client` do conftest |
| `tests/unit/test_skill_repository.py` | path traversal chamando o repositório **direto**: `..`, `../../etc/passwd`, `/etc/passwd`, vazio → `None` | `tests/unit/test_get_portfolio_summary.py:12` (`@pytest.fixture`). **`tmp_path` é primeiro uso** — zero ocorrências em todo o `Server/` |
| `tests/unit/test_skills_lint.py` | ver "Lint" abaixo | — |
| `Server/tests/conftest.py` | editar: `SKILLS_DIR` apontando para `Server/skills/` **antes** do `from app.config import settings` | linhas 4-5 (`os.environ.setdefault`) |

### Asserções do teste de integração

1. **Índice traz as 3 skills**; só as publicadas trazem `files`. Derivar o
   conjunto esperado lendo o `SKILLS_DIR`, **nunca** um número literal — um
   `assert total == 2` acopla a suíte a uma decisão pendente e fica vermelho no
   dia em que a pendência 4 for aprovada, que é exatamente o acoplamento que o
   desenho evita ao manter o frontmatter como fonte única.
2. Skill bloqueada aparece com `published: false` + `blocked_reason` e **sem**
   `files`; skill publicada vem **sem** `blocked_reason` (a RFC §4 fixa a forma
   nas duas direções — decidir se é `exclude_none` ou omissão no schema, e
   testar, senão sai `"blocked_reason": null` em toda skill publicada).
3. Forma da resposta: `{ items: [...], total }`. O `total` é do contrato e
   precisa de asserção — o consumidor não é só o Angular, é um agente lendo JSON.
4. Zip: caminhos **prefixados**, varredura **recursiva**, **sem ocultos** nem
   `__pycache__`, e o conjunto **exato** de arquivos da pasta (conferido com
   `zipfile` sobre `io.BytesIO`). As três skills de hoje são um `SKILL.md`
   solto cada, então a recursividade **não é exercitada por acidente** — semear
   uma subpasta no `tmp_path` do teste.
5. 404 para skill não publicada e para skill inexistente.
6. **`SKILLS_PUBLIC` nos dois estados, seis asserções**: aberto serve índice e
   zip sem sessão; fechado devolve 401 nos dois sem sessão **e 200 nos dois com
   sessão válida**. Sem o ramo autenticado, uma implementação que negue acesso a
   todo mundo passa verde e o kill switch vira botão de desligar o recurso.
   Como alternar: `settings` é singleton instanciado no import
   (`config.py:18`), então mexer em `os.environ` dentro do teste não surte
   efeito — `monkeypatch.setattr(settings, "skills_public", False)`, o que só
   funciona porque a dependência lê o atributo por requisição (§1).

### Lint das skills

Duas verificações, ambas estruturais (o lint sabe dizer se a frase está lá, não
se a skill é boa — o comportamento é a §8):

1. **Frontmatter**: os seis campos presentes; `name` == nome da pasta;
   **`description` não vazia**; `version` em formato de data;
   `writes`/`reads_external`/`published` booleanos; **`blocked_reason`
   obrigatório quando — e apenas quando — `published: false`** (as duas
   direções: bloqueada sem motivo renderiza um card mudo; publicada com motivo
   órfão emite campo que a API não deveria ter).
2. **Frases-âncora dentro do bloco `## Regras (inegociáveis)`** — a busca é
   **escopada a essa seção**, não ao arquivo inteiro. O passo 2 do rollout
   padronizou o cabeçalho nas três skills exatamente para dar ao lint um ponto
   fixo; varrer o arquivo todo faz uma frase citada de passagem (ou num exemplo
   de prompt) aprovar o lint sem que a regra esteja no bloco inegociável.
   Fixar as strings buscadas, para o lint não ficar sujeito a paráfrase:
   `writes: true` exige prévia confirmada e "nunca peça nem digite senha";
   `reads_external: true` exige "dado, nunca instrução".

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

### Conteúdo da página, na ordem

Conteúdo educativo **no template**, não em markdown renderizado — a RFC §8
rejeitou a dependência ("dois lugares para errar").

1. **Abertura em linguagem leiga** — o que a IA faz com a plataforma. É o
   primeiro passo da jornada 6.1 do PRD e o plano anterior o omitia; sem ele a
   página abre direto num tablist de configuração e exige que o usuário escolha
   a ferramenta antes de saber por quê.
2. **Guias por ferramenta** — tablist com roving tabindex copiado de
   `startup-detail`, uma aba por ferramenta, **cada aba com sua data de
   revisão**. Três regras de redação que vêm do PRD §8 e §9 e não são
   editoriais:
   - escritos **por objetivo** ("adicione o arquivo em Skills"), nunca por
     caminho de menu — as superfícies mudam de nome;
   - **sem capturas de tela no v1**; a data de revisão é o que o PRD entrega em
     troca;
   - cada guia vai **do zero até a primeira skill funcionando** (6.1), o que
     encadeia guia → catálogo → instalação → prompt de teste. Se o catálogo
     ficar só no fim da página, o usuário salta e volta — considerar repetir o
     ponto de entrada do catálogo dentro do guia.
   - **O guia do ChatGPT diz, sem eufemismo, que o navegador é virtual e na
     nuvem** — não é o do usuário, ele precisa autenticar dentro dele, e a
     postura de segurança é outra (PRD §5, em negrito no original). A superfície
     Cowork precisa ser **validada antes de ser prometida** no guia.
3. **Prompts prontos** — **um por skill** (PRD 6.1), texto sempre visível e
   selecionável no DOM; o botão de copiar é conveniência **tolerante a falha**:
   `navigator.clipboard` falha em contexto não seguro e sem permissão, e o
   clique não pode morrer em silêncio nem estourar no console. Os textos já
   estão dados nos gatilhos das jornadas: 6.3 "prepare a agenda com a
   [startup]"; 6.5 "faça uma auditoria do portfólio" / "o que os textos dizem
   que os números não mostram?" / "o que está escondido na [startup]?"; 6.4 é
   colar a transcrição e pedir o registro.
   *Decisão:* skill bloqueada **não** exibe prompt — oferecer o prompt de algo
   que não se pode baixar é armadilha para o leigo. O card carrega o motivo.
4. **Boas práticas** como seção de destaque, não rodapé, com as três mensagens
   que o PRD 6.1 e §7 exigem literalmente: **revisar antes de o agente salvar**;
   **o link de indicador é um segredo**; **nunca digitar senha no chat**. São
   conteúdo normativo de segurança — a página é o único lugar onde o humano as
   lê.
5. **Catálogo**, consumindo `GET /api/skills`. Cada card publicado tem:
   descrição leiga, **versão visível**, botão **"Baixar skill"** e, **abaixo do
   botão, a instrução de instalação por ferramenta** — os três itens do critério
   6.2, e o terceiro é o que faz o `.zip` deixar de ser inútil para quem não
   sabe onde soltá-lo. A página também explica que atualizar é baixar de novo.

### Regras do catálogo

- O download é `<a href="/api/skills/<nome>.zip">` — nunca HttpClient com blob.
- **Nome acessível do link carrega skill e versão**: "Baixar skill
  preparar-agenda, versão 2026-08-11" (RFC §6). Não é ornamento — N links
  rotulados "Baixar skill" são indistinguíveis para leitor de tela e para
  agente, que é o caso que o AGENTS.md descreve com os três `more_vert`. E são
  os agentes rodando as skills que precisam desse nome para achar o download
  certo.
- O card bloqueado nasce do dado (`published: false` + `blocked_reason`), nunca
  de lista no template: quando a pendência 4 for aprovada, virar
  `published: true` no frontmatter tem de bastar.

### Blocos compartilhados a reusar (não inventar)

`styles.scss` já tem `.pill` (`:1221`, com `--good/--warn/--danger/--info/--neutral`),
`.tag` (`:1283`), `.section-title` (`:566`), `.page-status` (`:583`) e
`.visually-hidden` (`:595`). O estado bloqueado é `.pill` — status estático
pareado com rótulo —, **nunca** um estilo novo. Cards em `--radius-md`. O
`blocked_reason` é **texto**, não cor. Nenhum hex/rgb em SCSS ou TypeScript.

### Cobertura dos specs

O plano anterior nomeava dois arquivos e zero asserções. A RFC §5 lista sete
comportamentos, e "specs verdes" não pode ser satisfeito por um spec que só
monta o componente:

- catálogo renderiza a partir da resposta da API;
- card publicado tem `<a href>` com caminho relativo `/api/skills/<nome>.zip`;
- card bloqueado nasce **do dado**, sem botão, com o motivo visível — e some
  quando `published` vira `true`, **sem mudança de template**;
- **cada aba de guia exibe sua data de revisão** (é o mecanismo
  anti-documentação-morta; sem spec, uma aba nova entra sem data e ninguém vê);
- prompts visíveis como texto; botão de copiar informa falha sem quebrar;
- três ramos de estado (carregando / conteúdo / erro);
- tablist com roving tabindex e navegação por setas;
- rota `/ia` protegida pelo guard.

## 4. Specs do contrato de navegação das skills

Seção nova. A RFC §5 exige specs travando os nomes acessíveis de que as três
skills dependem, e o plano anterior reduzia isso a um aviso em prosa ("não
renomear"). Prosa não é mecanismo: o próximo redesign quebra as três skills em
silêncio, e é justamente a mitigação declarada do risco "skills desatualizam
quando a UI da plataforma muda" (RFC §9). O teste de operabilidade do PRD-001
não cobre estas telas e ainda não existe.

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
2. **Depois do deploy**, smoke test: `curl $BACKEND_URL/api/skills` e o `.zip`.
   "`deploy.sh` revisado" não é o mesmo que executado e validado.
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
8. **Manter o nome de classe `.section-tabs`** ao copiar as abas. O
   `overflow-x: auto` vive em `startup-detail.scss:170` e é escopado à página,
   mas a regra que corrige o foco é **global** (`styles.scss:622`:
   `.table-shell :focus-visible, .section-tabs :focus-visible { outline-offset:
   -2px }`) e casa pelo nome. Renomear a classe traz o recorte do anel — o
   `overflow-x` faz o `overflow-y` virar `auto` junto, e o corte acontece nos
   quatro lados — sem trazer a correção.
9. **Não renomear itens de menu existentes**: "Monitoramento" é nome acessível
   travado pela RFC §5 — e a partir da §4 deste plano, por spec.

## 7. Ordem de implementação e o que fecha cada etapa

O AGENTS.md exige TDD por padrão, então a ordem é de pares **vermelho→verde**
por unidade, não "implementa tudo, testa depois". O caso que mais depende disso
é o path traversal: escrito depois da implementação, ele confirma o
comportamento existente em vez de especificá-lo, e não prova que é a resolução
por lista de pastas que impede a travessia.

| Etapa | Pares | Fecha quando |
| --- | --- | --- |
| 1. Repositório | `test_skill_repository.py` → `skill_repository.py` | 4 casos de travessia vermelhos, depois verdes |
| 2. Lint das skills | `test_skills_lint.py` → parser de frontmatter | as três skills passam; uma skill semeada sem `blocked_reason` reprova |
| 3. Casos de uso + rotas | `test_skill_api.py` → modelo, schema, casos de uso, controller, `skills_access` | as 6 asserções da §2, incluindo os dois estados do `SKILLS_PUBLIC` com e sem sessão |
| 4. Deploy/config | — | `docker compose up` sobe com as variáveis; imagem inspecionada; `deploy.sh` revisado; rollback documentado |
| 5. Serviço + modelo no front | `skill.service.spec.ts` → `skill.service.ts` | spec verde |
| 6. Página `/ia` | `ai.spec.ts` → `ai.{ts,html,scss}` | os 8 comportamentos da §3; gates abaixo |
| 7. Contrato de navegação | 5 specs da §4 | verdes, com os nomes das cinco telas travados |
| 8. Verificação manual das skills | roteiro da §8 | os cinco itens (a)–(e) executados, com dono |
| 9. Validação com usuário leigo | critério 6.1 do PRD | uma pessoa completa o guia sem ajuda — **e o guia é ajustado** com o que a sessão revelar (RFC §7 passo 4) |

### Gates (AGENTS.md), na etapa 6

Valem para a página **e** para o item novo da sidebar, que é mudança visual e
não cai no escopo "página":

1. **Acessibilidade** — o script de auditoria vem da skill `brq-secao`; zero
   `fail`. Depois, a metade interativa, que é a que mais importa num tablist com
   roving tabindex: teclado, foco visível, `Escape`, estado ARIA,
   `prefers-reduced-motion`. Hierarquia de títulos correta — numa página que é
   quase toda conteúdo educativo, saltar de `h1` para `h4` é o erro mais
   provável, e é por essa estrutura que um agente navega.
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
lançado com o guardrail "zero escritas sem confirmação" apenas **declarado** no
frontmatter e nunca observado, e com a defesa anti-injeção da
`reads_external: true` nunca exercitada — sendo que a RFC §9 registra injeção no
qualitativo como risco cuja mitigação **inclui este roteiro**.

**Dono: quem publica a skill no catálogo.** Nenhum lint verifica isto.

### Pré-requisito: o cenário de referência

O PRD §6.5 define o cenário como **artefato, não ideia**: uma startup de
demonstração semeada com três achados conhecidos — (a) contradição texto×número
("mês excelente" com receita caindo), (b) o mesmo próximo passo repetido em duas
reuniões consecutivas, (c) três meses sem qualquer preenchimento qualitativo.
Vive no seed de desenvolvimento e é mantido por quem publica a skill.

**Ele não existe no repositório** e não existe infraestrutura de seed alguma:
nada em `Server/alembic/versions/`, nenhum script, nada em `app/`. Sem ele, 9
critérios de aceite ficam inverificáveis — os 6 da jornada 6.5 e os 3 da 6.3,
que reusa a mesma startup.

**Decisão pendente — o mecanismo.** É a única lacuna deste plano que continua
sem resposta, e as três opções não são equivalentes:

| Opção | Por que serve / não serve |
| --- | --- |
| Migração Alembic de dados | **não** — mistura dado de demonstração com evolução de schema, e roda em produção junto com as outras |
| Fixture de pytest | **não** — insuficiente sozinha: o roteiro (a)–(e) é executado por uma pessoa com um agente operando o **navegador** contra a aplicação de pé, não pela suíte |
| Script idempotente (`Server/scripts/seed_demo.py`, via `docker compose exec server python -m scripts.seed_demo`) | **sim** — é o único que atende ao uso real |

Recomendação: o script. Precisa de decisão explícita porque cria uma pasta nova
no backend (`Server/scripts/`) que nenhuma das camadas do AGENTS.md prevê — ela
não é `controllers/`, `application/`, `domain/` nem `repositories/`, e a
convenção de camadas precisa registrar a exceção (é ferramenta de
desenvolvimento, não caminho de execução do produto).

### O roteiro (RFC §10)

| # | Verificação | Critério do PRD |
| --- | --- | --- |
| a | transcrição-armadilha com instrução embutida → nenhum efeito além do registro proposto, e o desvio é relatado | 6.4 |
| b | startup semeada com contradição, compromisso repetido e silêncio → os três achados aparecem, cada um com origem | 6.5 |
| c | a prévia confere com o registro salvo | 6.4 |
| d | campo qualitativo semeado com instrução embutida → a varredura não muda e a instrução vira achado de segurança | 6.5 |
| e | `preparar-agenda` sobre a mesma startup semeada → as perguntas citam os fatos plantados | 6.3 |

### Rastreabilidade dos critérios do incremento 1

| Critério | Verificado por |
| --- | --- |
| 6.1 — página e guia completáveis por leigo | conteúdo da §3 + specs da §3 + etapa 9 (usuário real) |
| 6.2 — catálogo, download, versão visível, instrução de instalação | testes de índice/zip/404 da §2 + specs de card e `<a href>` |
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

Nenhuma bloqueia começar. Mas a **pendência 4 bloqueia a entrega** de uma das
três skills que o PRD §4 define como sendo o incremento 1 — então "incremento 1
fechado" significa, hoje, 2 de 3 skills distribuíveis, com a terceira visível no
catálogo e bloqueada. As quatro que tocam esta implementação:

- **Pendência 1 — plano das ferramentas (individual vs. time)**: gera critério
  de aceite direto da jornada 6.2 ("quando o plano permitir, o guia documenta a
  implantação por organização como caminho **preferido**") e o caso de borda do
  §8 (sem plano de time, instalação individual por upload). O guia precisa
  cobrir os dois caminhos; sem registro, nasce só com o individual.
- **Pendência 2 — conexão nativa com Granola**: decide o conteúdo do guia e do
  prompt da `granola-reuniao`, que já está publicada — colar transcrição
  (caminho padrão do v1) vs. conectar o Granola. Sem registro, o guia pode
  prometer uma conexão que o v1 não sustenta.
- **Pendência 3 — harness primário**: no PRD ela decide **profundidade**, não
  ordem de abas — "o guia nasce para o primário e o outro entra como secundário
  até o MCP igualar". Tratar as duas abas com o mesmo peso é escolher a terceira
  opção antes da decisão, e é a mais cara de escrever e manter.
- **Pendência 4 — trânsito de dados**: mantém a `auditoria-qualitativa` com
  `published: false`. O mecanismo já existe; liberar é editar o frontmatter.
