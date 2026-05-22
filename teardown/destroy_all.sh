#!/bin/bash
# ============================================================
# Script: teardown/destroy_all.sh
# Purpose: Delete ALL resources for an environment
# Usage: ./teardown/destroy_all.sh --env=dev
# ⚠️  WARNING: This is IRREVERSIBLE!
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
    echo -e "${YELLOW}Enter environment to destroy (dev/prod):${NC}"
    read -r ENVIRONMENT
fi

# Safety check for prod
if [ "$ENVIRONMENT" = "prod" ]; then
    echo -e "${RED}⚠️  WARNING: Destroying PRODUCTION environment!${NC}"
    echo "Type 'destroy-production' to confirm:"
    read -r CONFIRM
    if [ "$CONFIRM" != "destroy-production" ]; then
        log_error "Aborted! Production not destroyed."
    fi
fi

source "${SCRIPT_DIR}/../config/${ENVIRONMENT}.env"

echo "=================================================="
echo " ⚠️  DESTROYING: ${ENVIRONMENT} environment"
echo " Project: ${PROJECT_ID}"
echo " This is IRREVERSIBLE!"
echo "=================================================="

echo -e "${RED}Type 'yes' to confirm destruction:${NC}"
read -r CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted!"
    exit 0
fi

# ── Delete Cloud Run services ──────────────────────────────
log_step "Deleting Cloud Run services"
gcloud run services delete "${RAG_ENGINE_NAME}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --quiet 2>/dev/null && \
    log_success "Cloud Run deleted" || log_warn "Cloud Run not found"

# ── Delete Cloud Functions ─────────────────────────────────
log_step "Deleting Cloud Functions"
gcloud functions delete "${INGESTION_FUNCTION}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --quiet 2>/dev/null && \
    log_success "Cloud Function deleted" || log_warn "Function not found"

# ── Delete Vector Search ───────────────────────────────────
log_step "Deleting Vector Search resources"
INDEX_ID=$(gcloud ai indexes list \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --filter="displayName=hr-rag-index" \
    --format="value(name)" 2>/dev/null | head -1)

ENDPOINT_ID=$(gcloud ai index-endpoints list \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --filter="displayName=hr-rag-endpoint" \
    --format="value(name)" 2>/dev/null | head -1)

if [ -n "$ENDPOINT_ID" ]; then
    gcloud ai index-endpoints delete "${ENDPOINT_ID}" \
        --region="${REGION}" \
        --project="${PROJECT_ID}" \
        --quiet 2>/dev/null && \
        log_success "Endpoint deleted" || log_warn "Endpoint not found"
fi

if [ -n "$INDEX_ID" ]; then
    gcloud ai indexes delete "${INDEX_ID}" \
        --region="${REGION}" \
        --project="${PROJECT_ID}" \
        --quiet 2>/dev/null && \
        log_success "Index deleted" || log_warn "Index not found"
fi

# ── Delete GCS Buckets ─────────────────────────────────────
log_step "Deleting GCS buckets"
for BUCKET in "${DOCS_BUCKET}" "${PROCESSED_BUCKET}" \
              "${ARTIFACTS_BUCKET}" "${AUDIT_BUCKET}"; do
    gcloud storage rm -r "gs://${BUCKET}" \
        --project="${PROJECT_ID}" 2>/dev/null && \
        log_success "Deleted: gs://${BUCKET}" || \
        log_warn "Bucket not found: ${BUCKET}"
done

# ── Delete BigQuery datasets ───────────────────────────────
log_step "Deleting BigQuery datasets"
for DATASET in "hr_rag_metrics" "hr_rag_analytics"; do
    bq rm -r -f --project_id="${PROJECT_ID}" "${DATASET}" 2>/dev/null && \
        log_success "Deleted dataset: ${DATASET}" || \
        log_warn "Dataset not found: ${DATASET}"
done

# ── Delete Secrets ─────────────────────────────────────────
log_step "Deleting secrets"
for SECRET in "gemini-api-key" "rag-config"; do
    gcloud secrets delete "${SECRET}" \
        --project="${PROJECT_ID}" \
        --quiet 2>/dev/null && \
        log_success "Deleted secret: ${SECRET}" || \
        log_warn "Secret not found: ${SECRET}"
done

# ── Delete KMS keys ────────────────────────────────────────
log_step "Note: KMS keys cannot be deleted (GCP policy)"
log_info "Keys will be disabled instead"
gcloud kms keys versions disable 1 \
    --key="${SIGN_KEY}" \
    --keyring="${KEYRING_NAME}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}" 2>/dev/null && \
    log_success "Signing key disabled" || log_warn "Could not disable key"

# ── Delete networking ──────────────────────────────────────
log_step "Deleting networking resources"
gcloud compute routers nats delete "hr-rag-nat" \
    --router="hr-rag-router" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --quiet 2>/dev/null && \
    log_success "NAT deleted" || log_warn "NAT not found"

gcloud compute routers delete "hr-rag-router" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --quiet 2>/dev/null && \
    log_success "Router deleted" || log_warn "Router not found"

gcloud compute firewall-rules delete \
    "hr-rag-allow-internal" \
    "hr-rag-allow-health-checks" \
    --project="${PROJECT_ID}" \
    --quiet 2>/dev/null && \
    log_success "Firewall rules deleted" || log_warn "Rules not found"

gcloud compute networks subnets delete \
    "hr-rag-app-subnet" "hr-rag-data-subnet" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --quiet 2>/dev/null && \
    log_success "Subnets deleted" || log_warn "Subnets not found"

gcloud compute networks delete "hr-rag-vpc" \
    --project="${PROJECT_ID}" \
    --quiet 2>/dev/null && \
    log_success "VPC deleted" || log_warn "VPC not found"

echo ""
echo "=================================================="
log_success "Teardown complete for: ${ENVIRONMENT}"
echo ""
echo "Note: GCP Project still exists!"
echo "To delete project:"
echo "  gcloud projects delete ${PROJECT_ID}"
echo "=================================================="
