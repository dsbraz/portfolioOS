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
6. Com `EMAIL_BACKEND=smtp`, criar ou atualizar os jobs e agendamentos do envio
   mensal por e-mail (seção 8); sem isso, pausar os que existirem
7. Imprimir as URLs dos dois serviços

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

## 8. Envio mensal do link de indicadores

O link de indicadores do mês anterior é enviado por e-mail por dois **Cloud Run
Jobs** que rodam `scripts/dispatch_monthly_report.py` com a mesma imagem do
backend. O **Cloud Scheduler** dispara um no dia 10 (`--kind initial`) e o outro no
dia 20 (`--kind reminder`, só para quem ainda não preencheu). Nenhuma rota HTTP é
exposta, e o `./deploy.sh` cria e atualiza tudo isso (veja **Configuração**).

Só recebem as startups com **Enviar o link de indicadores por e-mail todo mês**
ligado, e só os executivos marcados como **Recebe o link mensal** que tenham
e-mail. Cada endereço recebe um e-mail só, mesmo que dois executivos o
compartilhem. O histórico aparece em **Links anteriores**. Um erro inesperado
numa startup é registrado no log e o job segue para as demais.

Cada envio é **reservado** no banco antes de o e-mail sair e o **resultado** é
gravado depois, em transações separadas. Rodar o job de novo é seguro: o que já
foi entregue é pulado, e só o que o servidor de e-mail **recusou** é tentado
outra vez — duas execuções ao mesmo tempo não reenviam a mesma falha. Se a
transmissão cair antes da resposta do servidor de e-mail (a mensagem pode ter
sido aceita) ou o resultado não puder ser gravado, o envio fica
**Não confirmado**: o log mostra `NÃO CONFIRMADO`, a execução termina com
código 1, e o job **não reenvia** esse e-mail sozinho — um e-mail repetido na
caixa de um executivo é pior do que uma lacuna visível. Confirme com o
destinatário; se não chegou, mande o link pelo painel. O lembrete do dia 20, se
o mês continuar sem preenchimento, sai normalmente.

O lembrete do dia 20 só sai para um endereço que recebeu o e-mail do dia 10 num
dia anterior. Quem não recebeu (envio ligado depois, executivo marcado depois,
e-mail trocado, ou envio do dia 10 com falha) recebe o e-mail do dia 10 no
lugar do lembrete; rodar o job de lembrete de novo no mesmo dia não manda o
lembrete logo em seguida.

`EMAIL_BACKEND=console` só imprime e é aceito apenas com `ENVIRONMENT`
`development` ou `local`; em qualquer outro ambiente o job se recusa a rodar.

### Configuração

O `./deploy.sh` cria e mantém tudo o que o envio precisa, a partir do
`.env.production`. Basta preencher as variáveis abaixo e rodar o deploy:

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `EMAIL_BACKEND` | `smtp` liga o envio; `console` ou ausente, desliga; outro valor interrompe o deploy | `smtp` |
| `SMTP_HOST` / `SMTP_PORT` | relay SMTP corporativo (porta padrão `587`) | `smtp.gmail.com` / `587` |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | conta remetente (senha de app); opcionais num relay por IP | `portfolio@empresa.com` |
| `SMTP_SENDER` | remetente exibido | `portfolioOS <portfolio@empresa.com>` |
| `SMTP_STARTTLS` | STARTTLS (padrão `true`) | `true` |
| `EMAIL_SIGNATURE` | assinatura no fim do e-mail; vazia, termina no agradecimento | `Equipe de Portfólio` |
| `APP_BASE_URL` | opcional: base do link enviado; padrão, a URL do frontend que o deploy obtém | `https://portfolio.empresa.com` |
| `SCHEDULER_REGION` | opcional: região do Cloud Scheduler; padrão, `GCP_REGION` | `southamerica-east1` |
| `SCHEDULER_SERVICE_ACCOUNT` | opcional: conta que dispara os jobs; padrão, a service account padrão do Compute | — |
| `MONTHLY_REPORT_JOB_NAME` | opcional: prefixo dos jobs e agendamentos (`-initial`, `-reminder`); padrão `portfolioos-monthly-report` | — |

`DATABASE_URL`, `SECRET_KEY` e `CLOUD_SQL_CONNECTION` são as mesmas do backend.

O relay pode ser o do Google Workspace (`smtp.gmail.com`, ou `smtp-relay.gmail.com`
com IP liberado) ou o do Microsoft 365 (`smtp.office365.com`). O domínio remetente
precisa de SPF/DKIM configurados para que os e-mails não caiam no spam — isso é
DNS do domínio, fora do deploy.

Com `EMAIL_BACKEND=smtp`, cada deploy:
1. ativa a API do Cloud Scheduler;
2. cria ou atualiza os Cloud Run Jobs `portfolioos-monthly-report-initial` e
   `portfolioos-monthly-report-reminder`, com a imagem recém-publicada e as
   variáveis acima (sem novas tentativas automáticas: o próprio job decide o que
   repetir);
3. dá `roles/run.invoker` nos jobs à conta que os dispara;
4. cria ou atualiza os agendamentos, dia 10 e dia 20 às 9h de
   `America/Sao_Paulo`, e reativa um agendamento pausado.

Sem `EMAIL_BACKEND=smtp`, o deploy não cria nada e **pausa** agendamentos que um
deploy anterior tenha criado: desligar o envio também é só uma mudança no
`.env.production`.

Os dias ficam em `MONTHLY_REPORT_SCHEDULES` no `deploy.sh`. Se mudar, mude também
`MONTHLY_REPORT_DAYS` em `Client/src/app/models/monthly-report.model.ts` (o
texto das telas).

### Rodar manualmente

```bash
gcloud run jobs execute portfolioos-monthly-report-initial --region REGION
```

Quando algum envio falha ou fica não confirmado, o job termina com código 1 e a
execução aparece como falha no console do Cloud Run. O motivo fica no log e na
coluna **Envio automático** de **Links anteriores**. O job abre uma conexão SMTP
só e a reaproveita para todos os destinatários; se o servidor de e-mail encerrar
a sessão antes de uma mensagem, ele reconecta e tenta de novo uma vez.

Uma startup com o envio ligado e nenhum executivo marcado com e-mail aparece no
log como `SEM DESTINATÁRIO` e no resumo final, sem marcar a execução como falha:
corrija o cadastro.

O período é sempre o mês anterior ao dia da execução. Para rodar de novo **depois
da virada do mês** (por exemplo, um lembrete que falhou no dia 20 e só foi
reexecutado no dia 1º), informe o mês, senão o job começa o mês seguinte:

```bash
gcloud run jobs execute portfolioos-monthly-report-reminder --region REGION \
  --args="-m,scripts.dispatch_monthly_report,--kind,reminder,--period,2026-10"
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
