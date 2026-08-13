# Plano de implementação — Incremento 1 do PRD-002 (IA na plataforma)

- **Branch:** `feat/ia-na-plataforma` (empilhada sobre o redesign e os documentos)
- **Fonte normativa:** [PRD-002](prd/002-ia-na-plataforma.md) · [RFC-002](rfc/002-ia-na-plataforma.md)
- **Última atualização:** 2026-08-13
- **Natureza:** artefato de trabalho — pode ser apagado quando o incremento fechar.

> Os caminhos e modelos abaixo foram **verificados no repositório**, não
> lembrados. Cada arquivo novo cita o arquivo existente que serve de molde.

## 0. Estado atual da branch

Já feito, e é o passo 1 da RFC §7:

- `skills/` → **`Server/skills/`**, dentro do contexto de build do backend.
  Verificado que chega à imagem: `deploy.sh:52` envia `./Server`,
  `Server/cloudbuild.yaml:9` builda com esse contexto, `Dockerfile.prod:8` faz
  `COPY . .` → `/app/skills`. Nenhum dos 10 padrões de `Server/.gcloudignore`
  filtra a pasta.
- As três skills carregam o contrato de frontmatter e o cabeçalho
  `## Regras (inegociáveis)` uniforme, que o lint usa como ponto fixo.

## 1. Backend do catálogo

Recurso `skill` **sem tabela e sem migração** — lê o filesystem. Segue a cadeia
`controllers → application → domain → repositories`.

| Arquivo | Ação | Molde |
| --- | --- | --- |
| `Server/app/domain/models/skill.py` | criar | `application/portfolio/readmodels.py:8` — único precedente de `@dataclass(frozen=True)`. **Não** registrar em `domain/models/__init__.py`: aquele arquivo é o registry do SQLAlchemy |
| `Server/app/domain/schemas/skill.py` | criar | `schemas/monthly_indicator.py:105` (schema montado à mão) e `schemas/common.py:9` (`PaginatedResponse`) |
| `Server/app/repositories/skill_repository.py` | criar | `repositories/monthly_indicator_repository.py:27` — diretório injetado no `__init__`, nunca lido de `config` dentro do repo |
| `Server/app/application/skill/list_skills.py` | criar | `application/startup/list_startups.py:5` |
| `Server/app/application/skill/get_skill_package.py` | criar | `application/startup/get_startup.py:7` — devolve `bytes \| None`; **proibido** importar `fastapi` ou schemas (fitness function em `tests/architecture/`) |
| `Server/app/controllers/skill_controller.py` | criar | `controllers/monthly_indicator_controller.py:49` — `public_router` sem prefixo próprio |
| `Server/app/config.py` | editar | acrescentar `skills_dir` e `skills_public` ao `Settings` |
| `Server/app/controllers/dependencies.py` | editar | provider **sem sessão** no molde de `_get_password_hasher:85`; e `skills_access` no molde de `verify_startup_exists:94` |
| `Server/app/main.py` | editar | incluir no bloco **público** (`main.py:51`), nunca na lista `protected`; fail-fast do `SKILLS_DIR` no `lifespan:29` |

Decisões que já estão fechadas na RFC e não se rediscutem ao codar: resolução
por lista de pastas conhecidas (nunca concatenar o parâmetro num caminho);
varredura recursiva ignorando ocultos e `__pycache__`; entradas do zip
prefixadas com o nome da skill; `published: false` fora do zip e presente no
índice com `blocked_reason`.

**Primeiro uso de `fastapi.responses` no projeto** — hoje nenhum controller
retorna `Response` cru. O zip sai com `media_type="application/zip"` e
`Content-Disposition: attachment`.

## 2. Testes do backend

| Arquivo | Cobre | Molde |
| --- | --- | --- |
| `tests/integration/test_skill_api.py` | índice só com publicadas (hoje 2 de 3); bloqueada com `published:false` + `blocked_reason` e sem `files`; zip com caminhos prefixados (conferir com `zipfile` sobre `io.BytesIO`); 404 para não publicada e inexistente; `SKILLS_PUBLIC` nos dois estados | `tests/integration/test_user_invite_api.py:12` (fixture `anon_client`, `@pytest.mark.asyncio` explícito) |
| `tests/unit/test_skill_repository.py` | path traversal chamando o repositório **direto**: `..`, `../../etc/passwd`, `/etc/passwd`, vazio → `None` | `tests/unit/test_get_portfolio_summary.py:12`, com `tmp_path` |
| `tests/unit/test_skills_lint.py` | frontmatter completo, `name` == pasta, `version` como data, booleanos; frases-âncora conforme `writes` e `reads_external` | — |
| `Server/tests/conftest.py` | editar: `SKILLS_DIR` apontando para `Server/skills/` **antes** do `from app.config import settings` | linhas 4-5 |

O `conftest` não é opcional: o default `/app/skills` só existe dentro do
container, e o fail-fast quebraria a coleta ao rodar a suíte no host.

## 3. Página `/ia`

| Arquivo | Ação | Molde |
| --- | --- | --- |
| `Client/src/app/models/skill.model.ts` | criar | `models/startup.model.ts` |
| `Client/src/app/services/skill.service.ts` | criar | `services/startup.service.ts:12` — URL **relativa** (`/api/skills`) |
| `Client/src/app/pages/ia/ia.{ts,html,scss}` | criar | `pages/portfolio/*` (três ramos de estado, `aria-busy` no container) e `pages/users/users.scss:4` (bloco `.page-head`, que **não** é global) |
| `Client/src/app/app.routes.ts` | editar | copiar o bloco de `users:34` — `canActivate: [authGuard]`, **sem** `data: { public: true }` |
| `Client/src/app/app.html` | editar | novo `<li>` copiando o item Usuários (`app.html:52`), com `ariaCurrentWhenActive="page"` |
| specs: `ia.spec.ts`, `skill.service.spec.ts` | criar | `pages/portfolio/portfolio.spec.ts:13` e `services/startup.service.spec.ts:11` |

Conteúdo da página, na ordem: **guias por ferramenta** (tablist com roving
tabindex copiado de `startup-detail`, cada aba com sua data de revisão),
**prompts prontos** (texto selecionável no DOM, copiar como conveniência),
**boas práticas** e **catálogo**.

O download é `<a href="/api/skills/<nome>.zip">` — nunca HttpClient com blob.
O card bloqueado nasce do dado (`published: false` + `blocked_reason`), nunca
de lista no template: quando a pendência 4 for aprovada, virar
`published: true` no frontmatter tem de bastar.

## 4. Deploy e configuração

| Arquivo | Mudança |
| --- | --- |
| `deploy.sh:65` | duas linhas no heredoc: `SKILLS_DIR: "${SKILLS_DIR:-/app/skills}"` e `SKILLS_PUBLIC: "${SKILLS_PUBLIC:-true}"` — **com aspas**, porque `--env-vars-file` rejeita booleano YAML |
| `docker-compose.yml` | `SKILLS_PUBLIC` no `environment:` do serviço `server` (o `SKILLS_DIR` já funciona pelo mount) |
| `.env.production.example` | as duas variáveis comentadas com default explícito |
| `DEPLOY.md` | duas linhas na tabela de variáveis + o procedimento de flip emergencial do `SKILLS_PUBLIC` |

## 5. Armadilhas verificadas (não hipotéticas)

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
6. **`pyyaml` não está no `requirements.txt`.** Se o parser de frontmatter usar
   YAML, adicionar exige `docker compose build server` — o container de dev não
   reinstala dependências no reload.
7. **`.page-head` não é global**: cada página repete o bloco. Copiar de
   `users.scss`, não importar de outra página.
8. **`outline-offset: -2px`** ao copiar as abas — `.section-tabs` tem
   `overflow-x: auto`, o que recorta o anel de foco nos quatro lados.
9. **Não renomear itens de menu existentes**: "Monitoramento" é nome acessível
   travado pela RFC §5, do qual as três skills dependem.

## 6. Ordem sugerida e o que fecha cada etapa

| Etapa | Fecha quando |
| --- | --- |
| 1. Backend + testes | suíte verde, incluindo lint das três skills e path traversal |
| 2. Deploy/config | `docker compose up` sobe com as duas variáveis; `deploy.sh` revisado |
| 3. Serviço + modelo no front | spec do serviço verde |
| 4. Página `/ia` | specs verdes; auditoria de acessibilidade sem `fail`; revisão por imagem em 375/768/1440 nos dois temas |
| 5. Validação com usuário leigo | critério 6.1 do PRD — uma pessoa completa o guia sem ajuda |

## 7. Decisões que ainda dependem do Daniel

Nenhuma bloqueia começar. As duas que tocam esta implementação:

- **Pendência 3 — harness primário**: decide qual aba de guia vem primeiro.
  Implementar com as duas abas e a ordem definida no fim é seguro.
- **Pendência 4 — trânsito de dados**: mantém a `auditoria-qualitativa` com
  `published: false`. O mecanismo já existe; liberar é editar o frontmatter.

Uma decisão de nomenclatura que a implementação vai encontrar: a rota é `/ia`
(PT-BR) mas o AGENTS.md exige identificadores em EN-US. A convenção do
repositório é pasta == segmento da rota. Sugestão: manter a rota `/ia` (é UI,
e UI é PT-BR) e nomear a pasta/classe em EN-US (`pages/ai/`, `class Ai`),
registrando a exceção à convenção de espelhamento.
