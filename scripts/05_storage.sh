#!/bin/bash
# ============================================================
# Script: 05_storage.sh
# Purpose: Create GCS buckets, BigQuery datasets, Spanner
# Usage: ./scripts/05_storage.sh --env=dev
# ============================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config/common.env"

# ── Parse arguments ────────────────────────────────────────
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
echo " Enterprise HR RAG Platform - Storage Setup"
echo " Environment: ${ENVIRONMENT}"
echo " Project: ${PROJECT_ID}"
echo "=================================================="

# ── Helper: create bucket ──────────────────────────────────
create_bucket() {
    local BUCKET_NAME=$1
    local PURPOSE=$2

    if gcloud storage buckets describe "gs://${BUCKET_NAME}" &>/dev/null; then
        log_warn "Bucket ${BUCKET_NAME} already exists"
    else
        gcloud storage buckets create \
            -p "${PROJECT_ID}" \
            -l "${REGION}" \
            -b on \
            "gs://${BUCKET_NAME}"
        log_success "Bucket created: gs://${BUCKET_NAME} (${PURPOSE})"
    fi
}

# ── Create GCS Buckets ─────────────────────────────────────
log_step "Creating GCS buckets"

DOCS_BUCKET="${PROJECT_ID}-documents"
PROCESSED_BUCKET="${PROJECT_ID}-processed"
ARTIFACTS_BUCKET="${PROJECT_ID}-artifacts"
AUDIT_BUCKET="${PROJECT_ID}-audit-logs"

create_bucket "${DOCS_BUCKET}"      "HR policy documents"
create_bucket "${PROCESSED_BUCKET}" "Processed chunks"
create_bucket "${ARTIFACTS_BUCKET}" "Models and artifacts"
create_bucket "${AUDIT_BUCKET}"     "Audit logs (7-year retention)"

# Set 7-year retention on audit bucket
gcloud storage buckets update --retention-period 2557d "gs://${AUDIT_BUCKET}" 2>/dev/null && \
    log_success "7-year retention set on audit bucket" || \
    log_warn "Could not set retention on audit bucket"

# Set lifecycle on processed bucket (delete after 30 days)
cat > /tmp/lifecycle.json << LIFECYCLE
{
  "rule": [{
    "action": {"type": "Delete"},
    "condition": {"age": 30}
  }]
}
LIFECYCLE
gcloud storage buckets update --lifecycle-file=/tmp/lifecycle.json \
    "gs://${PROCESSED_BUCKET}" 2>/dev/null && \
    log_success "30-day lifecycle set on processed bucket" || \
    log_warn "Could not set lifecycle"
rm -f /tmp/lifecycle.json

# ── Create BigQuery Datasets ───────────────────────────────
log_step "Creating BigQuery datasets"

create_bq_dataset() {
    local DATASET=$1
    local DESCRIPTION=$2

    if bq ls --project_id="${PROJECT_ID}" "${DATASET}" &>/dev/null; then
        log_warn "Dataset ${DATASET} already exists"
    else
        bq mk \
            --project_id="${PROJECT_ID}" \
            --location="${REGION}" \
            --description="${DESCRIPTION}" \
            "${DATASET}"
        log_success "Dataset created: ${DATASET}"
    fi
}

create_bq_dataset "hr_rag_metrics"   "RAG evaluation metrics and RAGAS scores"
create_bq_dataset "hr_rag_analytics" "Usage analytics and query logs"

# Create tables
log_step "Creating BigQuery tables"

# Query logs table
bq mk --force \
    --project_id="${PROJECT_ID}" \
    --table \
    "hr_rag_metrics.query_logs" \
    "query_id:STRING,
     timestamp:TIMESTAMP,
     question:STRING,
     answer:STRING,
     latency_ms:INTEGER,
     chunks_retrieved:INTEGER,
     model_used:STRING,
     success:BOOLEAN" 2>/dev/null && \
    log_success "Table created: query_logs" || \
    log_warn "Table query_logs may already exist"

# Evaluation results table
bq mk --force \
    --project_id="${PROJECT_ID}" \
    --table \
    "hr_rag_metrics.evaluation_results" \
    "eval_id:STRING,
     timestamp:TIMESTAMP,
     faithfulness:FLOAT,
     answer_relevancy:FLOAT,
     context_precision:FLOAT,
     context_recall:FLOAT,
     overall_score:FLOAT,
     num_questions:INTEGER,
     config_chunk_size:INTEGER,
     config_top_k:INTEGER" 2>/dev/null && \
    log_success "Table created: evaluation_results" || \
    log_warn "Table evaluation_results may already exist"

# ── Create Cloud Spanner ───────────────────────────────────
log_step "Creating Cloud Spanner instance"

SPANNER_INSTANCE="hr-rag-instance"
SPANNER_DB="hr-rag-db"

if gcloud spanner instances describe "${SPANNER_INSTANCE}" \
    --project="${PROJECT_ID}" &>/dev/null; then
    log_warn "Spanner instance ${SPANNER_INSTANCE} already exists"
else
    gcloud spanner instances create "${SPANNER_INSTANCE}" \
        --project="${PROJECT_ID}" \
        --config="regional-${REGION}" \
        --description="HR RAG Platform metadata" \
        --processing-units="${SPANNER_PROCESSING_UNITS}"
    log_success "Spanner instance created: ${SPANNER_INSTANCE}"
fi

# Create database
if gcloud spanner databases describe "${SPANNER_DB}" \
    --instance="${SPANNER_INSTANCE}" \
    --project="${PROJECT_ID}" &>/dev/null; then
    log_warn "Spanner database ${SPANNER_DB} already exists"
else
    gcloud spanner databases create "${SPANNER_DB}" \
        --instance="${SPANNER_INSTANCE}" \
        --project="${PROJECT_ID}" \
        --database-dialect=GOOGLE_STANDARD_SQL \
        --ddl="
CREATE TABLE documents (
    document_id STRING(36) NOT NULL,
    filename STRING(255),
    category STRING(100),
    version INT64,
    status STRING(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    chunk_count INT64,
    file_size INT64,
    content_hash STRING(64),
) PRIMARY KEY (document_id);

CREATE TABLE chunks (
    document_id STRING(36) NOT NULL,
    chunk_id STRING(36) NOT NULL,
    chunk_text STRING(MAX),
    chunk_index INT64,
    page_number INT64,
    token_count INT64,
    embedding_model STRING(100),
) PRIMARY KEY (document_id, chunk_id),
INTERLEAVE IN PARENT documents ON DELETE CASCADE;

CREATE TABLE query_sessions (
    session_id STRING(36) NOT NULL,
    user_email STRING(255),
    created_at TIMESTAMP,
    last_active TIMESTAMP,
    query_count INT64,
) PRIMARY KEY (session_id);
"
    log_success "Spanner database created: ${SPANNER_DB}"
fi

# ── Save to config ─────────────────────────────────────────
cat >> "${SCRIPT_DIR}/../config/${ENVIRONMENT}.env" << ENVEOF

# Storage (auto-generated by 05_storage.sh)
export DOCS_BUCKET="${DOCS_BUCKET}"
export PROCESSED_BUCKET="${PROCESSED_BUCKET}"
export ARTIFACTS_BUCKET="${ARTIFACTS_BUCKET}"
export AUDIT_BUCKET="${AUDIT_BUCKET}"
export SPANNER_INSTANCE="${SPANNER_INSTANCE}"
export SPANNER_DB="${SPANNER_DB}"
ENVEOF

echo ""
echo "=================================================="
log_success "Storage setup complete!"
echo ""
echo "  GCS Buckets: 4 created"
echo "    📄 ${DOCS_BUCKET}"
echo "    ⚙️  ${PROCESSED_BUCKET}"
echo "    📦 ${ARTIFACTS_BUCKET}"
echo "    🔒 ${AUDIT_BUCKET}"
echo "  BigQuery: 2 datasets, 2 tables"
echo "  Spanner: ${SPANNER_INSTANCE}/${SPANNER_DB}"
echo ""
echo "Next step: ./scripts/06_vector_search.sh --env=${ENVIRONMENT}"
echo "=================================================="
