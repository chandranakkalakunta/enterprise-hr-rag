#!/bin/bash
# ============================================================
# Script: 06b_deploy_index.sh
# Purpose: Deploy Vector Search index to endpoint
# Usage: ./scripts/06b_deploy_index.sh --env=dev
# Run AFTER index creation is complete (check with list command)
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
echo " Deploying Vector Search Index to Endpoint"
echo "=================================================="

# Get index and endpoint IDs
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

if [ -z "$INDEX_ID" ] || [ -z "$ENDPOINT_ID" ]; then
    log_error "Index or endpoint not found! Run 06_vector_search.sh first!"
fi

log_info "Index: ${INDEX_ID}"
log_info "Endpoint: ${ENDPOINT_ID}"

# Check index is ready
# Check index is ready using shardsCount
# GCP quirk: state is empty when ready!
# Real indicator: indexStats.shardsCount > 0
SHARDS=$(gcloud ai indexes describe "${INDEX_ID}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --format="value(indexStats.shardsCount)" 2>/dev/null)

log_info "Index shardsCount: '${SHARDS}'"

if [ -z "${SHARDS}" ] || [ "${SHARDS}" -eq 0 ] 2>/dev/null; then
    log_error "Index not ready yet! shardsCount=0. Wait and try again!"
fi
log_success "Index is READY! shardsCount=${SHARDS}" 

log_step "Deploying index to endpoint..."

gcloud ai index-endpoints deploy-index "${ENDPOINT_ID}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --index="${INDEX_ID}" \
    --deployed-index-id="hr_rag_deployed_index" \
    --display-name="hr-rag-deployed-index" \
    --min-replica-count=1 \
    --max-replica-count=2

log_success "Index deployed to endpoint!"

# ── Wait for deployment to complete ──────────────────────────
log_step "Waiting for index deployment to complete..."
OPERATION_ID=$(echo "${OPERATION_NAME}" | rev | cut -d/ -f1 | rev)

for attempt in $(seq 1 20); do
    DONE=$(gcloud ai operations describe "${OPERATION_ID}" \
        --index-endpoint="${ENDPOINT_ID}" \
        --region="${REGION}" \
        --project="${PROJECT_ID}" \
        --format="value(done)" 2>/dev/null)
    if [ "${DONE}" = "True" ]; then
        log_success "Index deployment complete!"
        break
    fi
    log_info "Attempt ${attempt}/20 - still deploying... (30s)"
    sleep 30
done

echo ""
echo "=================================================="
log_success "Vector Search fully operational!"
echo "Next step: ./scripts/07_data_pipeline.sh --env=${ENVIRONMENT}"
echo "=================================================="
