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

echo "=================================================="
echo " Enterprise HR RAG Platform - RAG Deployment"
echo " Environment: ${ENVIRONMENT}"
echo " Project: ${PROJECT_ID}"
echo "=================================================="

IMAGE_NAME="asia-south1-docker.pkg.dev/${PROJECT_ID}/${REGISTRY_NAME}/hr-rag-engine"

# ── Build Docker image ─────────────────────────────────────
log_step "Building Docker image"

# Check Dockerfile exists
if [ ! -f "${SCRIPT_DIR}/../Dockerfile" ]; then
    log_warn "Dockerfile not found! Creating basic one..."
    cat > "${SCRIPT_DIR}/../Dockerfile" << 'DOCKEREOF'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
COPY src/ ./src/
EXPOSE 8080
CMD ["streamlit", "run", "src/ui/app.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
DOCKEREOF
fi

docker buildx build \
    --platform linux/amd64 \
    -t "${IMAGE_NAME}:latest" \
    --push \
    "${SCRIPT_DIR}/.."

log_success "Docker image built and pushed!"

# ── Get correct digest ─────────────────────────────────────
log_step "Getting image digest"

DIGEST=$(gcloud container images list-tags \
    "${IMAGE_NAME}" \
    --project="${PROJECT_ID}" \
    --sort-by="~timestamp" \
    --limit=1 \
    --format="value(digest)" 2>/dev/null)

FULL_IMAGE="${IMAGE_NAME}@sha256:${DIGEST}"
log_info "Image: ${FULL_IMAGE}"

# ── Sign image with KMS ────────────────────────────────────
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
    --update-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
    --set-env-vars="PROJECT_ID=${PROJECT_ID},ENVIRONMENT=${ENVIRONMENT},REGION=${REGION}" \
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
    --format="value(status.url)")

log_success "RAG Engine deployed: ${SERVICE_URL}"

echo ""
echo "=================================================="
log_success "RAG deployment complete!"
echo ""
echo "  Service: ${RAG_ENGINE_NAME}"
echo "  URL: ${SERVICE_URL}"
echo "  Environment: ${ENVIRONMENT}"
echo ""
echo "Test it:"
echo "  curl ${SERVICE_URL}/health"
echo ""
echo "Next step: ./scripts/09_monitoring.sh --env=${ENVIRONMENT}"
echo "=================================================="
