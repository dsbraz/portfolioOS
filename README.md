# Portfolio Manager

Sistema de gestao de portfolio para fundos de venture capital. Permite acompanhar startups investidas, indicadores mensais, reunioes de conselho, equipe executiva, pipeline de deals, e coleta de relatorios via formulario publico.

## Stack

| Camada     | Tecnologia                          |
|------------|-------------------------------------|
| Frontend   | Angular 21, Angular Material, SCSS  |
| Backend    | FastAPI, SQLAlchemy 2 (async), Pydantic |
| Banco      | PostgreSQL 17                       |
| Infra      | Docker Compose                      |
| Testes     | Vitest (frontend), pytest (backend) |

## Inicio rapido

### Pre-requisitos

- [Docker](https://docs.docker.com/get-docker/) e Docker Compose instalados

### 1. Clone e configure

```bash
git clone <repo-url> && cd portfolio
cp .env.example .env
```

O `.env` padrao ja vem com valores funcionais para desenvolvimento local.

### 2. Suba o ambiente

```bash
docker compose up --build
```

Isso inicia tres servicos:

| Servico  | URL / Porta               |
|----------|---------------------------|
| Client   | http://localhost:4200      |
| Server   | http://localhost:8000      |
| Postgres | localhost:5432             |

As migrations do banco rodam automaticamente na inicializacao do servidor.

### 3. Verifique

- Abra http://localhost:4200 no navegador &mdash; voce deve ver a tela de login.
- Acesse http://localhost:8000/api/health para confirmar o backend.

## Estrutura do repositorio

```
portfolio/
├── Client/                 # Angular frontend
│   └── src/app/
│       ├── components/     # Componentes reutilizaveis (status-badge, health-bar, kpi-card)
│       ├── guards/         # Auth guard (protecao de rotas)
│       ├── interceptors/   # Auth interceptor (JWT em requests HTTP)
│       ├── pages/          # Paginas / rotas
│       │   ├── login/                 # Tela de login
│       │   ├── portfolio/             # Monitoramento do portfolio
│       │   ├── startups/              # Detalhe + formularios (indicadores, reunioes, executivos, tokens)
│       │   ├── dealflow/              # Board kanban de deals
│       │   ├── users/                 # Gestao de usuarios
│       │   ├── ai/                    # Install-once AI package and capability catalog (/ia)
│       │   └── report/                # Formulario publico de indicadores mensais
│       ├── services/       # Comunicacao HTTP com a API
│       └── models/         # Interfaces TypeScript
│
├── Server/                 # FastAPI backend
│   ├── app/
│   │   ├── controllers/    # Rotas HTTP (camada de apresentacao)
│   │   ├── application/    # Use cases (camada de aplicacao)
│   │   ├── domain/
│   │   │   ├── models/     # Entidades SQLAlchemy (startup, deal, monthly_indicator, monthly_indicator_token, ...)
│   │   │   ├── schemas/    # Schemas Pydantic (request/response)
│   │   │   ├── exceptions.py # Excecoes de dominio
│   │   │   └── validators.py # Validadores compartilhados
│   │   ├── infrastructure/ # Adaptadores (bcrypt, JWT)
│   │   └── repositories/   # Acesso a dados
│   ├── alembic/            # Migrations do banco
│   ├── scripts/            # Ferramentas locais, incluindo o seed de demonstracao
│   ├── skills/             # Source of truth for the complete AI package and internal skills
│   └── tests/              # Testes automatizados (pytest)
│       ├── integration/    # Testes de API (rotas end-to-end)
│       ├── unit/           # Testes unitarios (use cases, validators)
│       └── architecture/   # Fitness functions (boundaries entre camadas)
│
├── CLAUDE.md               # Convencoes e principios de engenharia
├── AGENTS.md               # Instrucoes para agentes AI
└── docker-compose.yml      # Orquestracao dos servicos
```

## Arquitetura

### Backend &mdash; fluxo obrigatorio

```
Controller  ->  Application  ->  Domain  ->  Repository
 (HTTP)        (use cases)     (entidades)   (banco)
```

Controllers sao finos: validam entrada, delegam para use cases e mapeiam erros HTTP.
Use cases contem regras de negocio e orquestram repositorios.
Domain e livre de framework. Repositories encapsulam SQLAlchemy.
Infrastructure fornece adaptadores concretos (bcrypt para senhas, JWT para tokens).

### Frontend

```
Pages (rotas)  ->  Services (HTTP)  ->  Models (tipos)
      \-> Components (UI reutilizavel)
```

Componentes standalone do Angular 21 com signals para estado reativo.
Rotas protegidas por auth guard; requests autenticados via interceptor JWT.

## Entidades do dominio

```
Startup
├── Monthly Indicator        (1:N, indicadores financeiros mensais)
├── Monthly Indicator Token  (1:N, tokens para coleta publica de indicadores)
├── Board Meeting            (1:N, atas de reunioes de conselho)
└── Executive                (1:N, membros da equipe executiva)

Deal                    (entidade independente, pipeline de novos negocios)
User                    (entidade independente, usuarios do sistema)
```

### Startup

Registro de uma empresa investida. Campos principais: nome, setor, status (saudavel / atencao / critico), data do investimento.

### Monthly Indicator

KPIs mensais por startup: receita total, % receita recorrente, margem bruta, saldo de caixa, headcount, EBITDA/burn. Unico por startup + mes + ano.

### Board Meeting

Registro de reunioes de conselho: data, participantes, resumo, pontos de atencao, proximos passos.

### Executive

Membro do time executivo de uma startup: nome, cargo, contato, LinkedIn.

### Monthly Indicator Token

Token unico (UUID) vinculado a uma startup + mes + ano. Permite que a startup preencha seus indicadores mensais via formulario publico, sem autenticacao.

### Deal

Card no pipeline de deal flow. Colunas do kanban: Novo, Conversando, Analisando, Comite, Investido, Arquivado.

### User

Usuario do sistema com autenticacao via JWT. Campos: username, email, senha (hash bcrypt), status ativo.

## Endpoints da API

Base: `http://localhost:8000/api`

Public routes are `/health`, `/health/ready`, `/auth/login`,
`/monthly-indicator/{token}` (GET and POST), `/skills`, and `/skills.zip`.
All skill routes, including the legacy individual archive endpoint, require a
valid session when `SKILLS_PUBLIC=false`. All other routes require a JWT bearer
token.

| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/health` | Health check |
| GET | `/health/ready` | Readiness check |
| POST | `/auth/login` | Autenticacao (retorna JWT) |
| GET | `/skills` | Explain published and blocked capabilities; this catalog is not an installation selector |
| GET | `/skills.zip` | Download the complete install-once package as `portfolioos.zip` |
| GET | `/portfolio` | Resumo do portfolio (KPIs) |
| GET/POST | `/startups` | Listar / criar startups |
| GET/PATCH/DELETE | `/startups/{id}` | Detalhe / atualizar / remover startup |
| GET/POST | `/startups/{id}/monthly-indicators` | Indicadores mensais |
| GET/PATCH/DELETE | `/startups/{id}/monthly-indicators/{iid}` | Operacoes em indicador |
| GET/POST | `/startups/{id}/meetings` | Reunioes de conselho |
| GET/PATCH/DELETE | `/startups/{id}/meetings/{mid}` | Operacoes em reuniao |
| GET/POST | `/startups/{id}/executives` | Executivos |
| GET/PATCH/DELETE | `/startups/{id}/executives/{eid}` | Operacoes em executivo |
| POST/GET | `/startups/{id}/monthly-indicator-tokens` | Gerar / listar tokens de indicadores |
| GET/POST | `/deals` | Listar / criar deals |
| GET/PATCH/DELETE | `/deals/{id}` | Operacoes em deal |
| PATCH | `/deals/{id}/move` | Mover deal entre colunas |
| GET | `/monthly-indicator/{token}` | Obter contexto do formulario publico |
| POST | `/monthly-indicator/{token}` | Enviar indicadores via formulario publico |
| POST | `/users` | Criar usuario |
| GET | `/users` | Listar usuarios |
| PATCH | `/users/{id}` | Atualizar usuario |

Respostas de listagem retornam `{ items: T[], total: number }`.

### AI package distribution

The `/ia` page exposes one Stripe-like install-once artifact. Its single CTA
requests `/api/skills.zip` through the authenticated frontend service and saves
`portfolioos.zip`. The same file installs in ChatGPT and Claude.

The archive is a single Agent Skill. Its one `SKILL.md`, at the root of the
`portfolioos/` folder, routes requests to the workflow guides bundled under
`skills/<name>/GUIDE.md`: the broad `operar-portfolioos` base guide plus every
published specialized guide. Upload validators accept exactly one `SKILL.md`
per archive, so internal workflows are never packaged as nested skills.

For Granola meeting requests, the package probes an available Granola MCP
connection first. If it cannot use that source, it asks for the shared
`notes.granola.ai` conversation link; copied transcript text is only a last
resort.

Users never choose or download an individual skill. `/api/skills` only explains
capabilities and release status. A blocked capability such as
`auditoria-qualitativa` remains visible with its reason but is excluded from the
archive. Updating means downloading and reinstalling the complete package.

## Comandos do dia a dia

Todos os comandos assumem que os containers estao rodando (`docker compose up`).

```bash
# Rebuild apos alterar dependencias (package.json ou requirements.txt)
docker compose build server client

# Rodar migrations manualmente
docker compose exec server alembic upgrade head

# Criar nova migration
docker compose exec server alembic revision --autogenerate -m "descricao"

# Testes frontend
docker compose exec client npx ng test

# Testes backend
docker compose exec server pytest

# Restaurar o cenario deterministico para validar as skills de IA
docker compose exec server python -m scripts.seed_demo

# Logs de um servico especifico
docker compose logs -f server
```

## Variaveis de ambiente

Definidas no `.env` (gitignored). Copie de `.env.example`:

| Variavel | Descricao | Padrao |
|----------|-----------|--------|
| `POSTGRES_USER` | Usuario do banco | `portfolio` |
| `POSTGRES_PASSWORD` | Senha do banco | `portfolio123` |
| `POSTGRES_DB` | Nome do banco | `portfolio_db` |
| `POSTGRES_HOST` | Host do banco | `db` |
| `POSTGRES_PORT` | Porta do banco | `5432` |
| `DATABASE_URL` | Connection string completa (asyncpg) | montada a partir das variaveis acima |
| `ENVIRONMENT` | Ambiente de execucao; o seed de IA exige `development` | `development` |
| `SKILLS_DIR` | Diretorio das skills no backend | `/app/skills` |
| `SKILLS_PUBLIC` | Permite indice e downloads sem autenticacao | `true` |

## Convencoes

### Codigo

- **Python**: PEP 8, 4 espacos, `snake_case` funcoes/modulos, `PascalCase` classes.
- **TypeScript**: 2 espacos, `camelCase` variaveis/metodos, `PascalCase` classes/componentes.

### Commits

Conventional Commits obrigatorio:

```
feat: add portfolio endpoint
fix: handle missing database_url
chore: update dependencies
```

### PRs

- Resumo claro e escopo definido.
- Evidencia de testes.
- Screenshots para mudancas de UI.

Para detalhes completos sobre convencoes, testes e principios de engenharia, consulte o [CLAUDE.md](CLAUDE.md).
