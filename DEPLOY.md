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
2. Fazer deploy do backend no Cloud Run com conexão ao Cloud SQL
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

## 7. Migrations

As migrations rodam automaticamente na inicialização do backend (via lifespan handler). Para execução manual:

```bash
gcloud run jobs execute portfolioos-migrate --region YOUR_REGION
```

Ou conecte via Cloud SQL Auth Proxy localmente:

```bash
cloud-sql-proxy YOUR_PROJECT:YOUR_REGION:portfolioos-db &
alembic upgrade head
```

## 8. Troubleshooting

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
