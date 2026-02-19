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

# --- Step 2: Deploy backend to Cloud Run ---
echo ">>> Deploying backend..."

ENV_VARS_FILE=$(mktemp)
cat > "$ENV_VARS_FILE" <<ENVEOF
DATABASE_URL: "${DATABASE_URL}"
SECRET_KEY: "${SECRET_KEY}"
ENVIRONMENT: "production"
ENVEOF

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

echo ""
echo "=== Deployment complete ==="
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo "API docs: $BACKEND_URL/docs"
