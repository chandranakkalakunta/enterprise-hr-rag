#!/bin/bash
# ============================================================
# Script: 08_rag_deployment.sh
# Purpose: Build, sign and deploy RAG engine to Cloud Run
# Usage: ./scripts/08_rag_deployment.sh --env=dev
# ============================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config/common.env"

ENVIRONMENT=""
for arg in "$@"; do
    case $arg in
        --env=*) ENVIRONMENT="${arg#*=}" ;;
    esac
done

if [ -z "$ENVIRONMENT" ]; then
    echo -e "${YELLOW}Enter environment (dev/prod):${NC}"
    read -r ENVIRONMENT
fi

source "${SCRIPT_DIR}/../config/${ENVIRONMENT}.env"

IMAGE_NAME="${REGISTRY_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REGISTRY_NAME}/hr-rag-engine"

echo "=================================================="
echo " Enterprise HR RAG Platform - RAG Deployment"
echo " Environment: ${ENVIRONMENT}"
echo " Project: ${PROJECT_ID}"
echo " Image: ${IMAGE_NAME}"
echo "=================================================="

# ── Build Docker image ─────────────────────────────────────
log_step "Authenticating Docker to Artifact Registry"
gcloud auth configure-docker "${REGISTRY_LOCATION}-docker.pkg.dev" --quiet
log_success "Docker authenticated!"


log_step "Building Docker image" 


# Use Cloud Build - no local Docker needed!
gcloud builds submit \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --gcs-log-dir="gs://${PROJECT_ID}_cloudbuild/logs" \
    --gcs-source-staging-dir="gs://${PROJECT_ID}_cloudbuild/source" \
    --tag="${IMAGE_NAME}:latest" \
    "${SCRIPT_DIR}/.." 2>&1 | tail -5

log_success "Docker image built and pushed!"

# ── Get correct digest ─────────────────────────────────────
log_step "Getting image digest"


DIGEST=$(gcloud container images list-tags \
    "${IMAGE_NAME}" \
    --project="${PROJECT_ID}" \
    --sort-by="~timestamp" \
    --limit=1 \
    --format="json" 2>/dev/null | python3 -c \
    "import json,sys; d=json.load(sys.stdin); print(d[0]['digest']) if d else print('')")

FULL_IMAGE="${IMAGE_NAME}@${DIGEST}"
log_info "Digest: ${DIGEST:0:23}..."

# ── Sign image ─────────────────────────────────────────────
log_step "Signing image with KMS (Binary Authorization)"

gcloud beta container binauthz attestations sign-and-create \
    --artifact-url="${FULL_IMAGE}" \
    --attestor="${ATTESTOR_ID}" \
    --attestor-project="${PROJECT_ID}" \
    --keyversion-project="${PROJECT_ID}" \
    --keyversion-location="${REGION}" \
    --keyversion-keyring="${KEYRING_NAME}" \
    --keyversion-key="${SIGN_KEY}" \
    --keyversion=1 \
    --project="${PROJECT_ID}" 2>/dev/null && \
    log_success "Image signed!" || \
    log_warn "Signing failed or already signed"

# ── Deploy to Cloud Run ────────────────────────────────────
log_step "Deploying to Cloud Run"

gcloud run deploy "${RAG_ENGINE_NAME}" \
    --image="${FULL_IMAGE}" \
    --platform=managed \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --service-account="${RAG_SA}" \
    --update-secrets="GEMINI_API_KEY=gemini-api-key:latest,DB_PASSWORD=hr-db-password:latest" \
    --set-env-vars="PROJECT_ID=${PROJECT_ID},ENVIRONMENT=${ENVIRONMENT},REGION=${REGION},DOCS_BUCKET=${DOCS_BUCKET},DB_INSTANCE_NAME=${DB_INSTANCE_NAME},DB_NAME=${DB_NAME},DB_USER=${DB_USER}" \
    --memory="${MEMORY}" \
    --cpu="${CPU}" \
    --min-instances="${MIN_INSTANCES}" \
    --max-instances="${MAX_INSTANCES}" \
    --port=8080 \
    --allow-unauthenticated \
    --binary-authorization=default \
    --quiet

SERVICE_URL=$(gcloud run services describe "${RAG_ENGINE_NAME}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --format="value(status.url)" 2>/dev/null)

log_success "Deployed: ${SERVICE_URL}"

echo ""
echo "=================================================="
log_success "RAG deployment complete!"
echo ""
echo "  URL: ${SERVICE_URL}"
echo ""
echo "Test:"
echo "  curl ${SERVICE_URL}/_stcore/health"
echo "=================================================="
