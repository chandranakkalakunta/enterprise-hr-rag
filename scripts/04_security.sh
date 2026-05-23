#!/bin/bash
# ============================================================
# Script: 04_security.sh
# Purpose: Create service accounts, KMS, secrets, Binary Auth
# Usage: ./scripts/04_security.sh --env=dev
# ============================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config/common.env"

# ── Parse arguments ────────────────────────────────────────
ENVIRONMENT=""
GEMINI_KEY=""

for arg in "$@"; do
    case $arg in
        --env=*)        ENVIRONMENT="${arg#*=}" ;;
        --gemini-key=*) GEMINI_KEY="${arg#*=}" ;;
    esac
done

if [ -z "$ENVIRONMENT" ]; then
    echo -e "${YELLOW}Enter environment (dev/prod):${NC}"
    read -r ENVIRONMENT
fi

source "${SCRIPT_DIR}/../config/${ENVIRONMENT}.env"

# Prompt for Gemini key if not set
if [ -z "$GEMINI_KEY" ] && [ -z "${GEMINI_API_KEY:-}" ]; then
    echo -e "${YELLOW}Enter Gemini API Key:${NC}"
    read -rs GEMINI_KEY
    echo ""
else
    GEMINI_KEY="${GEMINI_KEY:-$GEMINI_API_KEY}"
fi

echo "=================================================="
echo " Enterprise HR RAG Platform - Security Setup"
echo " Environment: ${ENVIRONMENT}"
echo " Project: ${PROJECT_ID}"
echo "=================================================="

# ── Helper: create SA if not exists ───────────────────────
create_sa() {
    local SA_NAME=$1
    local DISPLAY_NAME=$2
    local SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

    if gcloud iam service-accounts describe "${SA_EMAIL}" \
        --project="${PROJECT_ID}" &>/dev/null; then
        log_warn "SA ${SA_NAME} already exists" >&2
    else
        gcloud iam service-accounts create "${SA_NAME}" \
            --display-name="${DISPLAY_NAME}" \
            --project="${PROJECT_ID}" >&2
        log_success "SA created: ${SA_EMAIL}" >&2
    fi
    echo "${SA_EMAIL}"
}

# ── Helper: grant IAM role ─────────────────────────────────
grant_role() {
    local MEMBER=$1
    local ROLE=$2
    if gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${MEMBER}" \
        --role="${ROLE}" \
        --quiet --format="none" 2>/dev/null; then
        log_success "Granted ${ROLE} to ${MEMBER}"
    else
        log_warn "Could not grant ${ROLE} to ${MEMBER} - may already exist"
    fi
}

# ── Create Service Accounts ────────────────────────────────
log_step "Creating service accounts"

RAG_SA=$(create_sa "rag-engine-sa" "RAG Engine Service Account")
INGEST_SA=$(create_sa "ingestion-sa" "Ingestion Pipeline Service Account")
EVAL_SA=$(create_sa "evaluation-sa" "Evaluation Pipeline Service Account")
CICD_SA=$(create_sa "cicd-sa" "CI/CD Pipeline Service Account")

# ── Grant IAM permissions ──────────────────────────────────
log_step "Granting IAM permissions"

# RAG Engine SA
grant_role "$RAG_SA" "roles/aiplatform.user"
grant_role "$RAG_SA" "roles/secretmanager.secretAccessor"
grant_role "$RAG_SA" "roles/spanner.databaseUser"
grant_role "$RAG_SA" "roles/storage.objectViewer"
grant_role "$RAG_SA" "roles/logging.logWriter"
grant_role "$RAG_SA" "roles/cloudtrace.agent"
grant_role "$RAG_SA" "roles/datastore.user"
grant_role "$RAG_SA" "roles/monitoring.metricWriter"

# Ingestion SA
grant_role "$INGEST_SA" "roles/storage.objectAdmin"
grant_role "$INGEST_SA" "roles/aiplatform.user"
grant_role "$INGEST_SA" "roles/dataflow.worker"
grant_role "$INGEST_SA" "roles/bigquery.dataEditor"
grant_role "$INGEST_SA" "roles/logging.logWriter"
grant_role "$INGEST_SA" "roles/eventarc.eventReceiver"
grant_role "$INGEST_SA" "roles/run.invoker"
grant_role "$INGEST_SA" "roles/datastore.user"

# Evaluation SA
grant_role "$EVAL_SA" "roles/bigquery.dataEditor"
grant_role "$EVAL_SA" "roles/aiplatform.user"
grant_role "$EVAL_SA" "roles/storage.objectViewer"
grant_role "$EVAL_SA" "roles/logging.logWriter"

# CI/CD SA
grant_role "$CICD_SA" "roles/run.admin"
grant_role "$CICD_SA" "roles/artifactregistry.writer"
grant_role "$CICD_SA" "roles/logging.logWriter"
grant_role "$CICD_SA" "roles/iam.serviceAccountUser"

# ── Grant GCS Service Agent permissions ───────────────────
log_step "Granting GCS service agent permissions"
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
GCS_SA="service-${PROJECT_NUMBER}@gs-project-accounts.iam.gserviceaccount.com"
grant_role_member() {
    local MEMBER=$1
    local ROLE=$2
    if gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="${MEMBER}" \
        --role="${ROLE}" \
        --quiet --format="none" 2>/dev/null; then
        log_success "Granted ${ROLE} to ${MEMBER}"
    else
        log_warn "Could not grant ${ROLE} to ${MEMBER}"
    fi
}
grant_role_member "serviceAccount:${GCS_SA}" "roles/pubsub.publisher"

# ── Create KMS Keyring ─────────────────────────────────────
log_step "Creating KMS keyring and keys"

KEYRING_NAME="hr-rag-keyring"
DATA_KEY="hr-rag-data-key"
SIGN_KEY="hr-rag-signing-key"

# Enable KMS
gcloud services enable cloudkms.googleapis.com \
    --project="${PROJECT_ID}" --quiet

# Create keyring
if gcloud kms keyrings describe "${KEYRING_NAME}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}" &>/dev/null; then
    log_warn "Keyring ${KEYRING_NAME} already exists"
else
    gcloud kms keyrings create "${KEYRING_NAME}" \
        --location="${REGION}" \
        --project="${PROJECT_ID}"
    log_success "KMS Keyring created: ${KEYRING_NAME}"
fi

# Create data encryption key
if gcloud kms keys describe "${DATA_KEY}" \
    --keyring="${KEYRING_NAME}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}" &>/dev/null; then
    log_warn "Key ${DATA_KEY} already exists"
else
    gcloud kms keys create "${DATA_KEY}" \
        --keyring="${KEYRING_NAME}" \
        --location="${REGION}" \
        --purpose=encryption \
        --rotation-period=7776000s \
        --next-rotation-time="$(date -u -v+90d +%Y-%m-%dT%H:%M:%SZ)" \
        --project="${PROJECT_ID}"
    log_success "Data encryption key created: ${DATA_KEY}"
fi

# Create signing key for Binary Authorization
if gcloud kms keys describe "${SIGN_KEY}" \
    --keyring="${KEYRING_NAME}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}" &>/dev/null; then
    log_warn "Key ${SIGN_KEY} already exists"
else
    gcloud kms keys create "${SIGN_KEY}" \
        --keyring="${KEYRING_NAME}" \
        --location="${REGION}" \
        --purpose=asymmetric-signing \
        --default-algorithm=rsa-sign-pkcs1-4096-sha512 \
        --project="${PROJECT_ID}"
    log_success "Signing key created: ${SIGN_KEY}"
fi

# ── Create Secrets ─────────────────────────────────────────
log_step "Creating secrets in Secret Manager"

create_secret() {
    local SECRET_NAME=$1
    local SECRET_VALUE=$2

    if gcloud secrets describe "${SECRET_NAME}" \
        --project="${PROJECT_ID}" &>/dev/null; then
        log_warn "Secret ${SECRET_NAME} already exists"
    else
        echo -n "${SECRET_VALUE}" | \
            gcloud secrets create "${SECRET_NAME}" \
            --data-file=- \
            --project="${PROJECT_ID}"
        log_success "Secret created: ${SECRET_NAME}"
    fi
}

# Create Gemini API key secret
create_secret "gemini-api-key" "${GEMINI_KEY}"

# Create RAG config secret
create_secret "rag-config" "{
    \"chunk_size\": ${CHUNK_SIZE},
    \"chunk_overlap\": ${CHUNK_OVERLAP},
    \"top_k_dense\": ${TOP_K_DENSE},
    \"top_k_sparse\": ${TOP_K_SPARSE},
    \"reranker_top_k\": ${RERANKER_TOP_K},
    \"hybrid_alpha\": ${HYBRID_ALPHA}
}"

# Grant RAG SA access to secrets
gcloud secrets add-iam-policy-binding "gemini-api-key" \
    --member="serviceAccount:${RAG_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --project="${PROJECT_ID}" --quiet
log_success "RAG SA granted access to gemini-api-key"

# ── Binary Authorization ───────────────────────────────────
log_step "Setting up Binary Authorization"

# Enable Binary Auth
gcloud services enable binaryauthorization.googleapis.com \
    --project="${PROJECT_ID}" --quiet

# Create attestor note
NOTE_ID="hr-rag-attestor-note"
ATTESTOR_ID="hr-rag-attestor"

curl -s -X POST \
    "https://containeranalysis.googleapis.com/v1/projects/${PROJECT_ID}/notes/?noteId=${NOTE_ID}" \
    --header "Authorization: Bearer $(gcloud auth print-access-token)" \
    --header "Content-Type: application/json" \
    --data "{
        \"name\": \"projects/${PROJECT_ID}/notes/${NOTE_ID}\",
        \"attestation\": {
            \"hint\": {\"human_readable_name\": \"HR RAG Attestor\"}
        }
    }" > /dev/null 2>&1 && \
    log_success "Attestor note created" || \
    log_warn "Attestor note may already exist"

# Create attestor
if gcloud container binauthz attestors describe "${ATTESTOR_ID}" \
    --project="${PROJECT_ID}" &>/dev/null; then
    log_warn "Attestor ${ATTESTOR_ID} already exists"
else
    gcloud container binauthz attestors create "${ATTESTOR_ID}" \
        --attestation-authority-note="${NOTE_ID}" \
        --attestation-authority-note-project="${PROJECT_ID}" \
        --project="${PROJECT_ID}"
    log_success "Attestor created: ${ATTESTOR_ID}"
fi

# Add KMS key to attestor
KEY_VERSION=$(gcloud kms keys versions list \
    --key="${SIGN_KEY}" \
    --keyring="${KEYRING_NAME}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}" \
    --filter="state=ENABLED" \
    --format="value(name)" \
    --limit=1)

gcloud container binauthz attestors public-keys add \
    --attestor="${ATTESTOR_ID}" \
    --keyversion="${KEY_VERSION}" \
    --project="${PROJECT_ID}" 2>/dev/null && \
    log_success "KMS key added to attestor" || \
    log_warn "Key may already be added to attestor"

# Set Binary Auth policy
POLICY_FILE=$(mktemp /tmp/binauthz-XXXXXX.yaml)
cat > "${POLICY_FILE}" << POLICY
globalPolicyEvaluationMode: ENABLE
defaultAdmissionRule:
  evaluationMode: REQUIRE_ATTESTATION
  enforcementMode: ENFORCED_BLOCK_AND_AUDIT_LOG
  requireAttestationsBy:
  - projects/${PROJECT_ID}/attestors/${ATTESTOR_ID}
POLICY
gcloud container binauthz policy import "${POLICY_FILE}" \
    --project="${PROJECT_ID}"
rm -f "${POLICY_FILE}"
log_success "Binary Authorization policy applied"



echo ""
echo "=================================================="
log_success "Security setup complete!"
echo ""
echo "  Service Accounts: 4 created"
echo "  KMS Keyring: ${KEYRING_NAME}"
echo "  KMS Keys: ${DATA_KEY}, ${SIGN_KEY}"
echo "  Secrets: gemini-api-key, rag-config"
echo "  Binary Authorization: ENFORCED"
echo ""
echo "Next step: ./scripts/05_storage.sh --env=${ENVIRONMENT}"
echo "=================================================="
