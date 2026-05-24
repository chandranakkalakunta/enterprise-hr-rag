#!/bin/bash
# ============================================================
# Script: ingest_documents.sh
# Purpose: Ingest all documents from GCS into RAG pipeline
# Usage: ./scripts/ingest_documents.sh --env=dev
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
echo " Enterprise HR RAG Platform - Document Ingestion"
echo " Environment: ${ENVIRONMENT}"
echo " Project: ${PROJECT_ID}"
echo " Bucket: ${DOCS_BUCKET}"
echo "=================================================="

# ── Check Python environment ───────────────────────────────
log_step "Checking Python environment"
PYTHON="${SCRIPT_DIR}/../venv/bin/python3"

if [ ! -f "${PYTHON}" ]; then
    log_error "Virtual environment not found! Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi
log_success "Python environment found"

# ── Check documents exist ──────────────────────────────────
log_step "Checking documents in GCS"
DOC_COUNT=$(gcloud storage ls "gs://${DOCS_BUCKET}/current/" \
    --project="${PROJECT_ID}" 2>/dev/null | wc -l | tr -d ' ')

if [ "$DOC_COUNT" -eq 0 ]; then
    log_error "No documents found in gs://${DOCS_BUCKET}/current/"
fi
log_success "Found ${DOC_COUNT} documents to ingest"

# ── Run ingestion pipeline ─────────────────────────────────
log_step "Running ingestion pipeline"

${PYTHON} << PYEOF
import sys
import os
import json
sys.path.insert(0, '${SCRIPT_DIR}/../src/ingestion')

os.environ['PROJECT_ID'] = '${PROJECT_ID}'
os.environ['REGION'] = '${REGION}'
os.environ['DOCS_BUCKET'] = '${DOCS_BUCKET}'

import os
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
from ingestion_pipeline import IngestionPipeline

pipeline = IngestionPipeline(
    project_id='${PROJECT_ID}',
    region='${REGION}',
    index_endpoint_id='${VECTOR_ENDPOINT_ID}',
    deployed_index_id='${DEPLOYED_INDEX_ID}',
    gemini_api_key=os.environ.get('GEMINI_API_KEY', ''),
    environment='${ENVIRONMENT}'
)

print("Ingesting all documents...")
results = pipeline.ingest_all_documents(
    bucket_name='${DOCS_BUCKET}',
    prefix='current/'
)

success = sum(1 for r in results if r['status'] == 'success')
failed  = sum(1 for r in results if r['status'] == 'failed')
total_chunks = sum(r.get('chunks', 0) for r in results)

print(f"\nINGESTION SUMMARY")
print(f"  Success: {success}/{len(results)}")
print(f"  Failed:  {failed}/{len(results)}")
print(f"  Total chunks: {total_chunks}")

for r in results:
    status = "OK" if r['status'] == 'success' else "FAIL"
    print(f"  [{status}] {r.get('filename','?')} → {r.get('chunks',0)} chunks")

sys.exit(0 if failed == 0 else 1)
PYEOF

if [ $? -eq 0 ]; then
    log_success "All documents ingested successfully!"
else
    log_warn "Some documents failed ingestion - check logs!"
fi

echo ""
echo "=================================================="
log_success "Ingestion complete!"
echo ""
echo "Verify in Firestore:"
echo "  https://console.cloud.google.com/firestore?project=${PROJECT_ID}"
echo "=================================================="
