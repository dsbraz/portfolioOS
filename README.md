# Portfolio Manager

Sistema de gestao de portfolio para fundos de venture capital. Permite acompanhar startups investidas, indicadores mensais, reunioes de conselho, equipe executiva e pipeline de deals.

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

- Abra http://localhost:4200 no navegador &mdash; voce deve ver o monitoramento do portfolio.
- Acesse http://localhost:8000/api/health para confirmar o backend.

## Estrutura do repositorio

```
portfolio/
├── Client/                 # Angular frontend
│   └── src/app/
│       ├── components/     # Componentes reutilizaveis (status-badge, health-bar, kpi-card)
│       ├── pages/          # Paginas / rotas
│       │   ├── portfolio-monitoring/ # Monitoramento do portfolio
│       │   ├── startups/           # Detalhe + formularios (indicadores, reunioes, executivos)
│       │   └── dealflow/           # Board kanban de deals
│       ├── services/       # Comunicacao HTTP com a API
│       └── models/         # Interfaces TypeScript
│
├── Server/                 # FastAPI backend
│   ├── app/
│   │   ├── controllers/    # Rotas HTTP (camada de apresentacao)
│   │   ├── services/       # Logica de negocio e orquestracao
│   │   ├── domain/
│   │   │   ├── models/     # Entidades SQLAlchemy
│   │   │   └── schemas/    # Schemas Pydantic (request/response)
│   │   └── repositories/   # Acesso a dados
│   ├── alembic/            # Migrations do banco
│   └── tests/              # Testes automatizados (pytest)
│
├── CLAUDE.md               # Convencoes e principios de engenharia
└── docker-compose.yml      # Orquestracao dos servicos
```

## Arquitetura

### Backend &mdash; fluxo obrigatorio

```
Controller  ->  Service  ->  Domain  ->  Repository
 (HTTP)       (regras)     (entidades)   (banco)
```

Controllers sao finos: validam entrada, delegam para o service e mapeiam erros HTTP.
Services contem regras de negocio e orquestram repositorios.
Domain e livre de framework. Repositories encapsulam SQLAlchemy.

### Frontend

```
Pages (rotas)  ->  Services (HTTP)  ->  Models (tipos)
      \-> Components (UI reutilizavel)
```

Componentes standalone do Angular 21 com signals para estado reativo.

## Entidades do dominio

```
Startup
├── Monthly Indicator   (1:N, indicadores financeiros mensais)
├── Board Meeting       (1:N, atas de reunioes de conselho)
└── Executive           (1:N, membros da equipe executiva)

Deal                    (entidade independente, pipeline de novos negocios)
```

### Startup

Registro de uma empresa investida. Campos principais: nome, setor, status (saudavel / atencao / critico), data do investimento.

### Monthly Indicator

KPIs mensais por startup: receita total, % receita recorrente, margem bruta, saldo de caixa, headcount, EBITDA/burn. Unico por startup + mes + ano.

### Board Meeting

Registro de reunioes de conselho: data, participantes, resumo, pontos de atencao, proximos passos.

### Executive

Membro do time executivo de uma startup: nome, cargo, contato, LinkedIn.

### Deal

Card no pipeline de deal flow. Colunas do kanban: Novo, Conversando, Analisando, Comite, Investido, Arquivado.

## Endpoints da API

Base: `http://localhost:8000/api`

| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/health` | Health check |
| GET | `/portfolio-monitoring/summary` | Resumo do portfolio (KPIs) |
| GET/POST | `/startups` | Listar / criar startups |
| GET/PATCH/DELETE | `/startups/{id}` | Detalhe / atualizar / remover startup |
| GET/POST | `/startups/{id}/indicators` | Indicadores mensais |
| GET/PATCH/DELETE | `/startups/{id}/indicators/{iid}` | Operacoes em indicador |
| GET/POST | `/startups/{id}/board_meetings` | Reunioes de conselho |
| GET/PATCH/DELETE | `/startups/{id}/board_meetings/{mid}` | Operacoes em reuniao |
| GET/POST | `/startups/{id}/executives` | Executivos |
| GET/PATCH/DELETE | `/startups/{id}/executives/{eid}` | Operacoes em executivo |
| GET/POST | `/deals` | Listar / criar deals |
| GET/PATCH/DELETE | `/deals/{id}` | Operacoes em deal |
| PATCH | `/deals/{id}/move` | Mover deal entre colunas |

Respostas de listagem retornam `{ items: T[], total: number }`.

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
