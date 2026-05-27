#!/bin/bash
# ============================================================
# Script: 11_cicd.sh
# Purpose: Grant Cloud Build permissions and create trigger
# Usage: ./scripts/11_cicd.sh --env=dev --repo=chandranakkalakunta/enterprise-hr-rag
# ============================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config/common.env"

ENVIRONMENT=""
GITHUB_REPO=""

for arg in "$@"; do
    case $arg in
        --env=*)  ENVIRONMENT="${arg#*=}" ;;
        --repo=*) GITHUB_REPO="${arg#*=}" ;;
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
echo " Project:     ${PROJECT_ID}"
echo "=================================================="

# ── Grant Cloud Build service account permissions ──────────
log_step "Granting Cloud Build SA permissions"

PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" \
    --format="value(projectNumber)")
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

for role in \
    "roles/run.admin" \
    "roles/iam.serviceAccountUser" \
    "roles/artifactregistry.writer" \
    "roles/binaryauthorization.attestorsVerifier" \
    "roles/cloudkms.signerVerifier" \
    "roles/containeranalysis.notes.attacher"; do
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${CB_SA}" \
        --role="${role}" \
        --quiet --format="none" 2>/dev/null && \
        log_success "Granted ${role}" || \
        log_warn "Could not grant ${role}"
done

# ── Create Cloud Build trigger ─────────────────────────────
if [ -n "${GITHUB_REPO}" ]; then
    log_step "Creating Cloud Build trigger for ${GITHUB_REPO}"

    gcloud builds triggers create github \
        --project="${PROJECT_ID}" \
        --region="${REGION}" \
        --repo-name="$(echo "${GITHUB_REPO}" | cut -d'/' -f2)" \
        --repo-owner="$(echo "${GITHUB_REPO}" | cut -d'/' -f1)" \
        --branch-pattern="^main$" \
        --build-config="cloudbuild.yaml" \
        --name="hr-rag-main-deploy-${ENVIRONMENT}" \
        --substitutions="\
_ENVIRONMENT=${ENVIRONMENT},\
_REGION=${REGION},\
_REGISTRY=${REGISTRY_NAME},\
_RRF_ALPHA=${RRF_ALPHA},\
_MEMORY=${MEMORY},\
_CPU=${CPU},\
_MIN_INSTANCES=${MIN_INSTANCES},\
_MAX_INSTANCES=${MAX_INSTANCES},\
_DOCS_BUCKET=${DOCS_BUCKET},\
_DB_INSTANCE_NAME=${DB_INSTANCE_NAME},\
_DB_NAME=${DB_NAME},\
_DB_USER=${DB_USER},\
_RAG_SA=${RAG_SA},\
_RAGAS_RELEVANCY_THRESHOLD=${RAGAS_RELEVANCY_THRESHOLD},\
_RAGAS_PRECISION_THRESHOLD=${RAGAS_PRECISION_THRESHOLD}" \
        --quiet 2>/dev/null && \
        log_success "Trigger created: hr-rag-main-deploy-${ENVIRONMENT}" || \
        log_warn "Trigger may already exist — skipping"
else
    log_warn "--repo not provided, skipping trigger creation"
    log_info "To create trigger later:"
    log_info "  ./scripts/11_cicd.sh --env=${ENVIRONMENT} --repo=<owner>/<repo>"
fi

echo ""
echo "=================================================="
log_success "CI/CD setup complete!"
echo ""
echo "  Cloud Build config: cloudbuild.yaml (in repo root)"
echo ""
echo "Trigger manually:"
echo "  gcloud builds submit --config=cloudbuild.yaml \\"
echo "    --project=${PROJECT_ID} --region=${REGION}"
echo ""
echo "View builds:"
echo "  https://console.cloud.google.com/cloud-build/builds?project=${PROJECT_ID}"
echo "=================================================="
