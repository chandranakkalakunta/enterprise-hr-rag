#!/bin/bash
# ============================================================
# Script: upload_documents.sh
# Purpose: Upload documents to GCS and trigger full pipeline
# Usage: ./scripts/upload_documents.sh --env=dev --dir=./data/documents
# ============================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config/common.env"

ENVIRONMENT=""
DOC_DIR="${SCRIPT_DIR}/../data/documents"

for arg in "$@"; do
    case $arg in
        --env=*)  ENVIRONMENT="${arg#*=}" ;;
        --dir=*)  DOC_DIR="${arg#*=}" ;;
    esac
done

if [ -z "$ENVIRONMENT" ]; then
    echo "Enter environment (dev/prod):"
    read -r ENVIRONMENT
fi

source "${SCRIPT_DIR}/../config/${ENVIRONMENT}.env"

echo "=================================================="
echo " Upload Documents + Full Ingestion Pipeline"
echo " Environment: ${ENVIRONMENT}"
echo " Source: ${DOC_DIR}"
echo " Bucket: gs://${DOCS_BUCKET}/current/"
echo "=================================================="

# ── Count documents ────────────────────────────────────────
log_step "Counting documents to upload"
DOC_COUNT=$(ls "${DOC_DIR}"/*.md "${DOC_DIR}"/*.pdf "${DOC_DIR}"/*.docx "${DOC_DIR}"/*.xlsx 2>/dev/null | wc -l | tr -d ' ')
if [ "$DOC_COUNT" -eq 0 ]; then
    log_error "No supported files found in ${DOC_DIR} (md/pdf/docx/xlsx)"
fi
log_success "Found ${DOC_COUNT} documents to upload"

# ── Upload to GCS ──────────────────────────────────────────
log_step "Uploading documents to GCS"
# Upload all supported formats
for ext in md pdf docx xlsx; do
    if ls "${DOC_DIR}"/*.${ext} 2>/dev/null | head -1 > /dev/null; then
        gcloud storage cp "${DOC_DIR}/"*.${ext} "gs://${DOCS_BUCKET}/current/" --project="${PROJECT_ID}"
    fi
done
log_success "Documents uploaded to gs://${DOCS_BUCKET}/current/"

# ── List uploaded documents ────────────────────────────────
log_step "Verifying GCS upload"
GCS_COUNT=$(gcloud storage ls "gs://${DOCS_BUCKET}/current/"     --project="${PROJECT_ID}" 2>/dev/null | wc -l | tr -d ' ')
log_success "GCS has ${GCS_COUNT} documents"

# ── Run ingestion pipeline ─────────────────────────────────
log_step "Running ingestion pipeline (cleanup + embed + index)"
"${SCRIPT_DIR}/ingest_documents.sh" --env="${ENVIRONMENT}"

# ── Verify ingestion ───────────────────────────────────────
log_step "Verifying ingestion"
"${SCRIPT_DIR}/verify_ingestion.sh" --env="${ENVIRONMENT}"

echo ""
echo "=================================================="
log_success "Upload and ingestion complete!"
echo ""
echo "Documents: ${DOC_COUNT}"
echo "Bucket: gs://${DOCS_BUCKET}/current/"
echo ""
echo "Next: make evaluate"
echo "=================================================="
