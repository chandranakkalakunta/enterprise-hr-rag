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
INDEX_STATE=$(gcloud ai indexes describe "${INDEX_ID}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --format="value(state)" 2>/dev/null)

if [ "${INDEX_STATE}" != "ACTIVE" ]; then
    log_error "Index not ready yet! State: ${INDEX_STATE}. Wait and try again!"
fi

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
echo ""
echo "=================================================="
log_success "Vector Search fully operational!"
echo "Next step: ./scripts/07_data_pipeline.sh --env=${ENVIRONMENT}"
echo "=================================================="
