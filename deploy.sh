#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Deploy portfolioOS to GCP Cloud Run + Cloud SQL
# =============================================================================
#
# Loads variables from .env.production (see .env.production.example).
# Variables can also be set/overridden via environment before running.
#
# Usage:
#   ./deploy.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env.production"

if [[ -f "$ENV_FILE" ]]; then
    echo ">>> Loading config from .env.production"
    set -a
    source "$ENV_FILE"
    set +a
else
    echo "WARNING: .env.production not found — using environment variables only" >&2
fi

# --- Validate required env vars ---
for var in GCP_PROJECT_ID GCP_REGION CLOUD_SQL_CONNECTION DATABASE_URL SECRET_KEY; do
    if [[ -z "${!var:-}" ]]; then
        echo "ERROR: $var is not set" >&2
        exit 1
    fi
done

# Same reading as the job's own (`build_email_sender`): trimmed, any case.
# Anything other than smtp/console is a typo, and guessing "off" would pause
# the e-mail without a word.
EMAIL_MODE=$(printf '%s' "${EMAIL_BACKEND:-console}" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
if [[ "$EMAIL_MODE" != "smtp" && "$EMAIL_MODE" != "console" ]]; then
    echo "ERROR: EMAIL_BACKEND must be smtp or console, got '${EMAIL_BACKEND}'" >&2
    exit 1
fi
if [[ "$EMAIL_MODE" == "smtp" ]]; then
    for var in SMTP_HOST SMTP_SENDER; do
        if [[ -z "${!var:-}" ]]; then
            echo "ERROR: EMAIL_BACKEND=smtp requires $var" >&2
            exit 1
        fi
    done
fi

# --- Defaults ---
BACKEND_SERVICE="${BACKEND_SERVICE_NAME:-portfolioos-server}"
FRONTEND_SERVICE="${FRONTEND_SERVICE_NAME:-portfolioos-client}"
BACKEND_MEMORY="${BACKEND_MEMORY:-512Mi}"
BACKEND_CPU="${BACKEND_CPU:-1}"
FRONTEND_MEMORY="${FRONTEND_MEMORY:-256Mi}"
FRONTEND_CPU="${FRONTEND_CPU:-1}"
REGISTRY="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/portfolioos"

echo "=== Deploying portfolioOS ==="
echo "Project:    $GCP_PROJECT_ID"
echo "Region:     $GCP_REGION"
echo "Cloud SQL:  $CLOUD_SQL_CONNECTION"
echo ""

# --- Step 1: Build and push backend image ---
echo ">>> Building backend image..."
gcloud builds submit ./Server \
    --config ./Server/cloudbuild.yaml \
    --substitutions "_IMAGE=${REGISTRY}/server:latest" \
    --project "$GCP_PROJECT_ID"

# A double-quoted YAML scalar: a secret with `"` or `\` must reach every
# service intact, or the backend and the jobs end up with different values.
yaml_quote() {
    local value=${1//\\/\\\\}
    value=${value//\"/\\\"}
    printf '"%s"' "$value"
}

# --- Step 2: Deploy backend to Cloud Run ---
echo ">>> Deploying backend..."

ENV_VARS_FILE=$(mktemp)
{
    echo "DATABASE_URL: $(yaml_quote "$DATABASE_URL")"
    echo "SECRET_KEY: $(yaml_quote "$SECRET_KEY")"
    echo "ACCESS_TOKEN_EXPIRE_MINUTES: $(yaml_quote "${ACCESS_TOKEN_EXPIRE_MINUTES:-60}")"
    echo "ENVIRONMENT: \"production\""
} > "$ENV_VARS_FILE"

gcloud run deploy "$BACKEND_SERVICE" \
    --image "${REGISTRY}/server:latest" \
    --platform managed \
    --region "$GCP_REGION" \
    --project "$GCP_PROJECT_ID" \
    --add-cloudsql-instances "$CLOUD_SQL_CONNECTION" \
    --env-vars-file "$ENV_VARS_FILE" \
    --memory "$BACKEND_MEMORY" \
    --cpu "$BACKEND_CPU" \
    --min-instances 0 \
    --max-instances 4 \
    --port 8080 \
    --startup-probe "httpGet.path=/api/health/ready,failureThreshold=10,periodSeconds=10,timeoutSeconds=5" \
    --allow-unauthenticated \
    --quiet

rm -f "$ENV_VARS_FILE"

# --- Step 3: Get backend URL ---
BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" \
    --region "$GCP_REGION" \
    --project "$GCP_PROJECT_ID" \
    --format "value(status.url)")

echo ">>> Backend deployed at: $BACKEND_URL"

# --- Step 4: Build and push frontend image ---
echo ">>> Building frontend image..."
gcloud builds submit ./Client \
    --config ./Client/cloudbuild.yaml \
    --substitutions "_IMAGE=${REGISTRY}/client:latest" \
    --project "$GCP_PROJECT_ID"

# --- Step 5: Deploy frontend to Cloud Run ---
echo ">>> Deploying frontend..."
gcloud run deploy "$FRONTEND_SERVICE" \
    --image "${REGISTRY}/client:latest" \
    --platform managed \
    --region "$GCP_REGION" \
    --project "$GCP_PROJECT_ID" \
    --set-env-vars "API_URL=${BACKEND_URL}" \
    --memory "$FRONTEND_MEMORY" \
    --cpu "$FRONTEND_CPU" \
    --min-instances 0 \
    --max-instances 4 \
    --port 8080 \
    --allow-unauthenticated \
    --quiet

# --- Step 6: Get frontend URL ---
FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE" \
    --region "$GCP_REGION" \
    --project "$GCP_PROJECT_ID" \
    --format "value(status.url)")

echo ">>> Frontend deployed at: $FRONTEND_URL"

# --- Step 7: Update backend CORS to include frontend URL ---
echo ">>> Updating backend CORS origins..."
CORS_ORIGINS="[\"${FRONTEND_URL}\"]"

gcloud run services update "$BACKEND_SERVICE" \
    --region "$GCP_REGION" \
    --project "$GCP_PROJECT_ID" \
    --update-env-vars "CORS_ORIGINS=${CORS_ORIGINS}" \
    --quiet

# --- Step 8: Monthly reporting e-mail (Cloud Run Jobs + Cloud Scheduler) ---
# One job per kind, so the schedule triggers it without overriding arguments
# and its service account needs only `run.invoker`. Every command here is
# create-or-update: rerunning the deploy converges, it never duplicates.
# The days are product copy too: keep them in sync with MONTHLY_REPORT_DAYS
# in Client/src/app/models/monthly-report.model.ts.
MONTHLY_REPORT_JOB_PREFIX="${MONTHLY_REPORT_JOB_NAME:-portfolioos-monthly-report}"
MONTHLY_REPORT_SCHEDULES=("initial:0 9 10 * *" "reminder:0 9 20 * *")
MONTHLY_REPORT_TIME_ZONE="America/Sao_Paulo"
SCHEDULER_REGION="${SCHEDULER_REGION:-$GCP_REGION}"

# Prints the schedule's state (ENABLED, PAUSED), or nothing when it does not
# exist. Any other failure stops the deploy: reading it as "missing" would
# create a duplicate, or leave running a schedule that should be paused.
schedule_state() {
    local out
    if out=$(gcloud scheduler jobs describe "$1" \
        --location "$SCHEDULER_REGION" --project "$GCP_PROJECT_ID" \
        --format "value(state)" 2>&1); then
        printf '%s' "$out"
        return 0
    fi
    if [[ "$out" == *NOT_FOUND* ]]; then
        return 0
    fi
    echo "ERROR: could not read schedule $1:" >&2
    echo "$out" >&2
    return 1
}

if [[ "$EMAIL_MODE" == "smtp" ]]; then
    echo ">>> Deploying monthly reporting e-mail jobs..."
    gcloud services enable cloudscheduler.googleapis.com --project "$GCP_PROJECT_ID"

    PROJECT_NUMBER=$(gcloud projects describe "$GCP_PROJECT_ID" --format "value(projectNumber)")
    SCHEDULER_SA="${SCHEDULER_SERVICE_ACCOUNT:-${PROJECT_NUMBER}-compute@developer.gserviceaccount.com}"

    JOB_ENV_FILE=$(mktemp)
    trap 'rm -f "$JOB_ENV_FILE"' EXIT
    {
        echo "DATABASE_URL: $(yaml_quote "$DATABASE_URL")"
        echo "SECRET_KEY: $(yaml_quote "$SECRET_KEY")"
        echo "ENVIRONMENT: \"production\""
        echo "APP_BASE_URL: $(yaml_quote "${APP_BASE_URL:-$FRONTEND_URL}")"
        echo "EMAIL_BACKEND: \"smtp\""
        echo "SMTP_HOST: $(yaml_quote "$SMTP_HOST")"
        echo "SMTP_SENDER: $(yaml_quote "$SMTP_SENDER")"
        # Optional: left out when blank, so Server/app/config.py stays the
        # only place that holds their defaults.
        for var in SMTP_PORT SMTP_STARTTLS SMTP_USERNAME SMTP_PASSWORD EMAIL_SIGNATURE; do
            if [[ -n "${!var:-}" ]]; then
                echo "${var}: $(yaml_quote "${!var}")"
            fi
        done
    } > "$JOB_ENV_FILE"

    for entry in "${MONTHLY_REPORT_SCHEDULES[@]}"; do
        KIND="${entry%%:*}"
        SCHEDULE="${entry#*:}"
        JOB="${MONTHLY_REPORT_JOB_PREFIX}-${KIND}"

        # `--max-retries 0`: the job decides what to retry; a blind rerun
        # by Cloud Run would only repeat the failures in the same minute.
        gcloud run jobs deploy "$JOB" \
            --image "${REGISTRY}/server:latest" \
            --region "$GCP_REGION" \
            --project "$GCP_PROJECT_ID" \
            --set-cloudsql-instances "$CLOUD_SQL_CONNECTION" \
            --env-vars-file "$JOB_ENV_FILE" \
            --command python \
            --args="-m,scripts.dispatch_monthly_report,--kind,${KIND}" \
            --max-retries 0 \
            --task-timeout 15m \
            --quiet

        gcloud run jobs add-iam-policy-binding "$JOB" \
            --region "$GCP_REGION" \
            --project "$GCP_PROJECT_ID" \
            --member "serviceAccount:${SCHEDULER_SA}" \
            --role "roles/run.invoker" \
            --quiet >/dev/null

        SCHEDULE_ARGS=(
            --location "$SCHEDULER_REGION"
            --project "$GCP_PROJECT_ID"
            --schedule "$SCHEDULE"
            --time-zone "$MONTHLY_REPORT_TIME_ZONE"
            --http-method POST
            --uri "https://run.googleapis.com/v2/projects/${GCP_PROJECT_ID}/locations/${GCP_REGION}/jobs/${JOB}:run"
            --oauth-service-account-email "$SCHEDULER_SA"
            --quiet
        )
        STATE=$(schedule_state "$JOB")
        if [[ -n "$STATE" ]]; then
            # The job takes no overrides: a body left by an older setup would
            # need more than `run.invoker` and fail every month.
            gcloud scheduler jobs update http "$JOB" "${SCHEDULE_ARGS[@]}" --clear-message-body
            if [[ "$STATE" == "PAUSED" ]]; then
                gcloud scheduler jobs resume "$JOB" \
                    --location "$SCHEDULER_REGION" --project "$GCP_PROJECT_ID" --quiet
            fi
        else
            gcloud scheduler jobs create http "$JOB" "${SCHEDULE_ARGS[@]}"
        fi
        echo ">>> ${JOB}: \"${SCHEDULE}\" (${MONTHLY_REPORT_TIME_ZONE})"
    done

    rm -f "$JOB_ENV_FILE"
else
    # Not configured: nothing is created, and a schedule left by an earlier
    # deploy is paused, so turning the e-mail off is also just an .env change.
    echo ">>> Monthly reporting e-mail off (EMAIL_BACKEND is not smtp)"
    # No API, no schedule to pause. A failed listing stops the deploy rather
    # than skip the pause.
    SCHEDULER_API=$(gcloud services list --enabled --project "$GCP_PROJECT_ID" \
        --filter "config.name=cloudscheduler.googleapis.com" --format "value(config.name)")
    if [[ -n "$SCHEDULER_API" ]]; then
        for entry in "${MONTHLY_REPORT_SCHEDULES[@]}"; do
            JOB="${MONTHLY_REPORT_JOB_PREFIX}-${entry%%:*}"
            STATE=$(schedule_state "$JOB")
            if [[ "$STATE" == "ENABLED" ]]; then
                gcloud scheduler jobs pause "$JOB" \
                    --location "$SCHEDULER_REGION" --project "$GCP_PROJECT_ID" --quiet
                echo ">>> ${JOB}: paused"
            fi
        done
    fi
fi

echo ""
echo "=== Deployment complete ==="
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo "API docs: $BACKEND_URL/docs"
