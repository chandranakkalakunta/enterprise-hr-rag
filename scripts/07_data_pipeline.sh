#!/bin/bash
# ============================================================
# Script: 07_data_pipeline.sh
# Purpose: Deploy Cloud Functions for auto document ingestion
# Usage: ./scripts/07_data_pipeline.sh --env=dev
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
echo " Enterprise HR RAG Platform - Data Pipeline Setup"
echo " Environment: ${ENVIRONMENT}"
echo " Project: ${PROJECT_ID}"
echo "=================================================="

# ── Create Cloud Function source ───────────────────────────
log_step "Creating Cloud Function source code"

mkdir -p /tmp/hr-rag-functions/ingest

cat > /tmp/hr-rag-functions/ingest/main.py << 'PYEOF'
"""
HR RAG Auto-Ingestion Cloud Function
Triggered when documents uploaded to GCS
"""
import functions_framework
import json
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.cloud_event
def ingest_document(cloud_event):
    """Triggered by GCS upload."""
    data = cloud_event.data
    bucket = data["bucket"]
    filename = data["name"]

    logger.info(f"Processing: {filename} from {bucket}")

    # Skip non-document files
    if not filename.endswith(('.pdf', '.docx', '.txt', '.html')):
        logger.info(f"Skipping non-document file: {filename}")
        return

    try:
        project_id = os.environ.get('PROJECT_ID', '')
        environment = os.environ.get('ENVIRONMENT', 'dev')

        logger.info(json.dumps({
            "event": "ingestion_triggered",
            "filename": filename,
            "bucket": bucket,
            "project_id": project_id,
            "environment": environment,
            "timestamp": datetime.utcnow().isoformat()
        }))

        # TODO: Phase 2 - Full RAG ingestion pipeline:
        # 1. Extract text (PDF/Word/Excel)
        # 2. Semantic chunking
        # 3. Generate embeddings (text-embedding-004)
        # 4. Update Vertex AI Vector Search
        # 5. Update Spanner metadata
        # 6. Update BM25 sparse index

        logger.info(f"✅ Ingestion triggered for: {filename}")

    except Exception as e:
        logger.error(f"Error processing {filename}: {str(e)}")
        raise
PYEOF

cat > /tmp/hr-rag-functions/ingest/requirements.txt << 'REQEOF'
functions-framework==3.*
google-cloud-storage==2.*
google-cloud-bigquery==3.*
google-cloud-spanner==3.*
REQEOF

log_success "Cloud Function source created"

# ── Deploy Cloud Function ──────────────────────────────────
log_step "Deploying auto-ingestion Cloud Function"

if gcloud functions describe "${INGESTION_FUNCTION}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" &>/dev/null; then
    log_warn "Function ${INGESTION_FUNCTION} already exists - updating"
    DEPLOY_CMD="deploy"
else
    DEPLOY_CMD="deploy"
fi

gcloud functions ${DEPLOY_CMD} "${INGESTION_FUNCTION}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --runtime=python311 \
    --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
    --trigger-event-filters="bucket=${DOCS_BUCKET}" \
    --source=/tmp/hr-rag-functions/ingest \
    --entry-point=ingest_document \
    --service-account="${INGEST_SA}" \
    --memory=512MB \
    --timeout=540s \
    --set-env-vars="PROJECT_ID=${PROJECT_ID},ENVIRONMENT=${ENVIRONMENT}" \
    --gen2 \
    --quiet && \
    log_success "Cloud Function deployed: ${INGESTION_FUNCTION}" || \
    log_warn "Cloud Function deployment failed - check logs"

# ── Create upload helper script ────────────────────────────
log_step "Creating document upload helper"

cat > "${SCRIPT_DIR}/upload_documents.sh" << 'UPLOADEOF'
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
UPLOADEOF

chmod +x "${SCRIPT_DIR}/upload_documents.sh"
log_success "Upload helper created: scripts/upload_documents.sh"

# ── Cleanup ────────────────────────────────────────────────
rm -rf /tmp/hr-rag-functions

echo ""
echo "=================================================="
log_success "Data pipeline setup complete!"
echo ""
echo "  Function: ${INGESTION_FUNCTION}"
echo "  Trigger:  GCS upload to ${DOCS_BUCKET}"
echo "  Runtime:  Python 3.11"
echo ""
echo "To upload documents:"
echo "  ./scripts/upload_documents.sh --env=${ENVIRONMENT}"
echo ""
echo "Next step: ./scripts/08_rag_deployment.sh --env=${ENVIRONMENT}"
echo "=================================================="
