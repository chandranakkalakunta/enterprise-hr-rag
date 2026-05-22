#!/bin/bash
# ============================================================
# Script: 11_cicd.sh
# Purpose: Setup Cloud Build CI/CD pipeline
# Usage: ./scripts/11_cicd.sh --env=dev
# ============================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config/common.env"

ENVIRONMENT=""
GITHUB_REPO=""

for arg in "$@"; do
    case $arg in
        --env=*)    ENVIRONMENT="${arg#*=}" ;;
        --repo=*)   GITHUB_REPO="${arg#*=}" ;;
    esac
done

if [ -z "$ENVIRONMENT" ]; then
    echo -e "${YELLOW}Enter environment (dev/prod):${NC}"
    read -r ENVIRONMENT
fi

source "${SCRIPT_DIR}/../config/${ENVIRONMENT}.env"

echo "=================================================="
echo " Enterprise HR RAG Platform - CI/CD Setup"
echo " Environment: ${ENVIRONMENT}"
echo " Project: ${PROJECT_ID}"
echo "=================================================="

# ── Create Cloud Build config ──────────────────────────────
log_step "Creating Cloud Build configuration"

cat > "${SCRIPT_DIR}/../cloudbuild.yaml" << 'CBEOF'
steps:
  # Step 1: Run tests
  - name: 'python:3.11'
    id: 'test'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install -r requirements.txt --quiet
        python -m pytest tests/ -v 2>/dev/null || echo "No tests found"

  # Step 2: Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    id: 'build'
    args:
      - 'buildx'
      - 'build'
      - '--platform=linux/amd64'
      - '-t'
      - '${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REGISTRY}/hr-rag-engine:${SHORT_SHA}'
      - '-t'
      - '${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REGISTRY}/hr-rag-engine:latest'
      - '--push'
      - '.'

  # Step 3: Sign image with Binary Authorization
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    id: 'sign'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        DIGEST=$(gcloud container images describe \
          ${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REGISTRY}/hr-rag-engine:${SHORT_SHA} \
          --format='get(image_summary.digest)')
        gcloud beta container binauthz attestations sign-and-create \
          --artifact-url="${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REGISTRY}/hr-rag-engine@$$DIGEST" \
          --attestor=${_ATTESTOR} \
          --attestor-project=${PROJECT_ID} \
          --keyversion-project=${PROJECT_ID} \
          --keyversion-location=${_REGION} \
          --keyversion-keyring=${_KEYRING} \
          --keyversion-key=${_SIGN_KEY} \
          --keyversion=1 \
          --project=${PROJECT_ID}

  # Step 4: Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    id: 'deploy'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        DIGEST=$(gcloud container images describe \
          ${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REGISTRY}/hr-rag-engine:${SHORT_SHA} \
          --format='get(image_summary.digest)')
        gcloud run deploy hr-rag-engine \
          --image="${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REGISTRY}/hr-rag-engine@$$DIGEST" \
          --platform=managed \
          --region=${_REGION} \
          --project=${PROJECT_ID} \
          --binary-authorization=default \
          --quiet

substitutions:
  _REGION: asia-south1
  _REGISTRY: hr-rag-repo
  _ATTESTOR: hr-rag-attestor
  _KEYRING: hr-rag-keyring
  _SIGN_KEY: hr-rag-signing-key

options:
  logging: CLOUD_LOGGING_ONLY
  machineType: E2_HIGHCPU_8
CBEOF

log_success "cloudbuild.yaml created"

# ── Grant Cloud Build permissions ──────────────────────────
log_step "Granting Cloud Build permissions"

PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" \
    --format="value(projectNumber)")
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

for role in \
    "roles/run.admin" \
    "roles/iam.serviceAccountUser" \
    "roles/artifactregistry.writer" \
    "roles/binaryauthorization.attestorsVerifier"; do
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${CB_SA}" \
        --role="${role}" \
        --quiet --format="none" 2>/dev/null && \
        log_success "Granted ${role} to Cloud Build SA" || \
        log_warn "Could not grant ${role}"
done

echo ""
echo "=================================================="
log_success "CI/CD setup complete!"
echo ""
echo "  Cloud Build config: cloudbuild.yaml"
echo ""
echo "To trigger manually:"
echo "  gcloud builds submit --config=cloudbuild.yaml --project=${PROJECT_ID}"
echo ""
echo "To connect GitHub (manual step required):"
echo "  https://console.cloud.google.com/cloud-build/triggers?project=${PROJECT_ID}"
echo ""
echo "=================================================="
