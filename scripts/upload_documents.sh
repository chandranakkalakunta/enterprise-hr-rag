#!/bin/bash
# ============================================================
# Script: upload_documents.sh
# Purpose: Upload HR documents to GCS for ingestion
# Usage: ./scripts/upload_documents.sh --env=dev --dir=./data/documents
# ============================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config/common.env"

ENVIRONMENT=""
DOC_DIR="./data/documents"

for arg in "$@"; do
    case $arg in
        --env=*) ENVIRONMENT="${arg#*=}" ;;
        --dir=*) DOC_DIR="${arg#*=}" ;;
    esac
done

if [ -z "$ENVIRONMENT" ]; then
    echo -e "${YELLOW}Enter environment (dev/prod):${NC}"
    read -r ENVIRONMENT
fi

source "${SCRIPT_DIR}/../config/${ENVIRONMENT}.env"

log_step "Uploading documents from ${DOC_DIR}"

DOC_COUNT=$(find "${DOC_DIR}" \( -name "*.pdf" -o -name "*.docx" -o -name "*.txt" \) | wc -l | tr -d ' ')
log_info "Found ${DOC_COUNT} documents to upload"

if [ "$DOC_COUNT" -eq 0 ]; then
    log_warn "No documents found in ${DOC_DIR}"
    exit 1
fi

gcloud storage cp "${DOC_DIR}/" \
    "gs://${DOCS_BUCKET}/" \
    --recursive \
    --project="${PROJECT_ID}"

log_success "Uploaded ${DOC_COUNT} documents to gs://${DOCS_BUCKET}/"
log_info "Auto-ingestion Cloud Function will trigger automatically!"
