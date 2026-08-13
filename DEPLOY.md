# Deploy em Produção — GCP Cloud Run + Cloud SQL

Guia para deploy do portfolioOS no Google Cloud Platform usando Cloud Run (backend + frontend) e Cloud SQL (PostgreSQL).

## Arquitetura

```
[Browser] → [Cloud Run: nginx (frontend)] → /api/ proxy → [Cloud Run: gunicorn (backend)] → [Cloud SQL: PostgreSQL]
```

- **Frontend**: build estático do Angular servido por nginx, com `/api/` encaminhado ao backend
- **Backend**: FastAPI com gunicorn + uvicorn workers
- **Banco de dados**: Cloud SQL PostgreSQL 17 (conectado via Unix socket do Cloud Run)

## Pré-requisitos

1. **Conta GCP** com billing ativado
2. **gcloud CLI** instalado e autenticado:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

## 1. Configuração do Projeto GCP

Crie um projeto (ou use um existente):

```bash
gcloud projects create YOUR_PROJECT_ID --name="PortfolioOS"
gcloud config set project YOUR_PROJECT_ID
```

Ative as APIs necessárias:

```bash
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    sqladmin.googleapis.com \
    cloudbuild.googleapis.com
```

Conceda as permissões necessárias à service account do Cloud Build:

```bash
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")
SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Acesso ao Cloud Storage (upload de artefatos de build)
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${SA}" --role="roles/storage.admin"

# Push de imagens no Artifact Registry
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${SA}" --role="roles/artifactregistry.writer"

# Escrita de logs do Cloud Build
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${SA}" --role="roles/logging.logWriter"

# Conexão ao Cloud SQL (necessário para o Cloud Run acessar o banco)
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${SA}" --role="roles/cloudsql.client"
```

## 2. Artifact Registry

Crie um repositório Docker para armazenar as imagens:

```bash
gcloud artifacts repositories create portfolioos \
    --repository-format=docker \
    --location=YOUR_REGION \
    --description="portfolioOS container images"
```

Autentique o Docker com o registry:

```bash
gcloud auth configure-docker YOUR_REGION-docker.pkg.dev
```

## 3. Cloud SQL

Crie a instância PostgreSQL:

```bash
gcloud sql instances create portfolioos-db \
    --database-version=POSTGRES_17 \
    --edition=ENTERPRISE \
    --tier=db-f1-micro \
    --region=YOUR_REGION \
    --storage-size=10GB \
    --storage-auto-increase
```

Crie o banco de dados e o usuário:

```bash
gcloud sql databases create portfolio_db --instance=portfolioos-db

gcloud sql users create portfolio \
    --instance=portfolioos-db \
    --password=YOUR_SECURE_PASSWORD
```

Obtenha o nome da conexão (necessário para o deploy):

```bash
gcloud sql instances describe portfolioos-db --format="value(connectionName)"
# Saída: YOUR_PROJECT_ID:YOUR_REGION:portfolioos-db
```

## 4. Variáveis de Ambiente

Copie o arquivo de exemplo e preencha com seus valores:

```bash
cp .env.production.example .env.production
```

Edite o `.env.production` com seus valores:

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `GCP_PROJECT_ID` | ID do projeto GCP | `my-project-123` |
| `GCP_REGION` | Região GCP | `us-central1` |
| `CLOUD_SQL_CONNECTION` | Nome da conexão Cloud SQL | `my-project:us-central1:portfolioos-db` |
| `DATABASE_URL` | URL PostgreSQL com Unix socket | Ver abaixo |
| `SECRET_KEY` | Chave secreta da aplicação (min 32 chars) | Gerar com `openssl rand -hex 32` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Validade do JWT de acesso (em minutos) | `60` |
| `SKILLS_DIR` | Diretório das skills dentro da imagem do backend | `/app/skills` |
| `SKILLS_PUBLIC` | Libera o índice e os pacotes sem autenticação | `true` |

**Formato da DATABASE_URL** (Unix socket do Cloud SQL):

```
postgresql+asyncpg://USUARIO:SENHA@/BANCO?host=/cloudsql/PROJETO:REGIAO:INSTANCIA
```

Exemplo:

```
postgresql+asyncpg://portfolio:SUA_SENHA@/portfolio_db?host=/cloudsql/my-project:us-central1:portfolioos-db
```

> O `.env.production` está no `.gitignore` — os segredos nunca saem da sua máquina.

## 5. Primeiro Deploy

```bash
chmod +x deploy.sh
./deploy.sh
```

O script vai:
1. Buildar e enviar a imagem do backend
2. Fazer deploy do backend no Cloud Run com conexão ao Cloud SQL e acesso às skills
3. Buildar e enviar a imagem do frontend
4. Fazer deploy do frontend no Cloud Run com `API_URL` apontando para o backend
5. Atualizar o CORS do backend para permitir a URL do frontend
6. Imprimir as URLs dos dois serviços

## 6. Deploys Seguintes

Basta executar o mesmo script novamente:

```bash
./deploy.sh
```

Para deploy de apenas um serviço, é possível buildar e fazer deploy manualmente:

```bash
# Somente backend
gcloud builds submit ./Server \
    --tag REGION-docker.pkg.dev/PROJECT/portfolioos/server:latest \
    --dockerfile=Dockerfile.prod

gcloud run deploy portfolioos-server \
    --image REGION-docker.pkg.dev/PROJECT/portfolioos/server:latest \
    --region REGION

# Somente frontend
gcloud builds submit ./Client \
    --tag REGION-docker.pkg.dev/PROJECT/portfolioos/client:latest \
    --dockerfile=Dockerfile.prod

gcloud run deploy portfolioos-client \
    --image REGION-docker.pkg.dev/PROJECT/portfolioos/client:latest \
    --region REGION
```

## 7. Verificação e contingência das skills

Antes de promover uma imagem do backend, confirme que a fonte única foi
incluída no build:

```bash
docker pull YOUR_REGION-docker.pkg.dev/YOUR_PROJECT_ID/portfolioos/server:latest
docker run --rm --entrypoint ls \
    YOUR_REGION-docker.pkg.dev/YOUR_PROJECT_ID/portfolioos/server:latest \
    -R /app/skills
```

After deploy, validate the explanatory catalog and the one complete package.
These anonymous commands assume `SKILLS_PUBLIC=true`:

```bash
curl --fail "$BACKEND_URL/api/skills"
curl --fail --output /tmp/portfolioos.zip \
    "$BACKEND_URL/api/skills.zip"
unzip -l /tmp/portfolioos.zip
```

With `SKILLS_PUBLIC=false`, use a temporary token for a non-production test
user and do not print or commit it:

```bash
curl --fail --header "Authorization: Bearer $PORTFOLIOOS_ACCESS_TOKEN" \
    "$BACKEND_URL/api/skills"
curl --fail --header "Authorization: Bearer $PORTFOLIOOS_ACCESS_TOKEN" \
    --output /tmp/portfolioos.zip \
    "$BACKEND_URL/api/skills.zip"
```

The archive must have one `portfolioos/` root containing `SKILL.md`,
`README.md`, `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, and
`skills/operar-portfolioos/` plus every published specialized skill.
`skills/auditoria-qualitativa/` must remain absent while its catalog record is
`published: false` (sourced from its hidden `.portfolioos.json`, which must also
remain absent from the archive).

### Fechamento emergencial do catálogo

To require a valid session on both routes, update the service and record the
same value in `.env.production` so the next deployment does not reopen them:

```bash
gcloud run services update portfolioos-server \
    --region YOUR_REGION \
    --update-env-vars SKILLS_PUBLIC=false
```

Use `SKILLS_PUBLIC=true` in the same command and in `.env.production` to restore
anonymous access. In closed mode, anonymous curl requests return 401; the
authenticated `/ia` page continues to download through `SkillService`, whose
HTTP request receives the bearer token from the auth interceptor.

### Rollback por falha no diretório

Se `/app/skills` estiver ausente, o backend falha no startup em vez de servir
um catálogo vazio. Direcione o tráfego à revisão saudável anterior enquanto a
imagem é corrigida:

```bash
gcloud run revisions list \
    --service portfolioos-server \
    --region YOUR_REGION

gcloud run services update-traffic portfolioos-server \
    --region YOUR_REGION \
    --to-revisions PREVIOUS_REVISION=100
```

## 8. Migrations

As migrations rodam automaticamente na inicialização do backend (via lifespan handler). Para execução manual:

```bash
gcloud run jobs execute portfolioos-migrate --region YOUR_REGION
```

Ou conecte via Cloud SQL Auth Proxy localmente:

```bash
cloud-sql-proxy YOUR_PROJECT:YOUR_REGION:portfolioos-db &
alembic upgrade head
```

## 9. Troubleshooting

### Conexão recusada ao Cloud SQL

- Verifique se a instância está rodando: `gcloud sql instances describe portfolioos-db`
- Confirme que `--add-cloudsql-instances` está configurado no serviço Cloud Run
- Confirme que a `DATABASE_URL` usa o formato Unix socket (`?host=/cloudsql/...`)

### Erros de CORS

- Verifique se `CORS_ORIGINS` no backend inclui a URL do frontend (com `https://`, sem barra final)
- Consulte com: `gcloud run services describe portfolioos-server --region REGION --format="value(spec.template.spec.containers[0].env)"`

### Frontend exibe página em branco / 404

- Verifique se o build do Angular gerou os arquivos em `dist/Client/browser/`
- Consulte os logs do nginx: `gcloud run services logs read portfolioos-client --region REGION`

### Health check falha (startup probe)

- Consulte os logs do backend: `gcloud run services logs read portfolioos-server --region REGION`
- O endpoint `/api/health/ready` testa a conexão com o banco — se falhar, a conexão com o Cloud SQL pode estar mal configurada

### Consultando logs

```bash
# Logs do backend
gcloud run services logs read portfolioos-server --region YOUR_REGION --limit 50

# Logs do frontend
gcloud run services logs read portfolioos-client --region YOUR_REGION --limit 50
```
