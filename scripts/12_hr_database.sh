#!/bin/bash
# ============================================================
# Script: 12_hr_database.sh
# Purpose: Create Cloud SQL PostgreSQL instance for HR data
# Usage: ./scripts/12_hr_database.sh --env=dev
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
    echo "Enter environment (dev/prod):"
    read -r ENVIRONMENT
fi

source "${SCRIPT_DIR}/../config/${ENVIRONMENT}.env"

echo "=================================================="
echo " ChandraAILabs HR RAG - HR Database Setup"
echo " Environment: ${ENVIRONMENT}"
echo " Project: ${PROJECT_ID}"
echo "=================================================="

# ── Enable APIs ────────────────────────────────────────────
log_step "Enabling Cloud SQL API"
gcloud services enable sqladmin.googleapis.com     --project="${PROJECT_ID}" --quiet
log_success "Cloud SQL API enabled"

# ── Create Cloud SQL instance ──────────────────────────────
log_step "Creating Cloud SQL PostgreSQL instance"

if gcloud sql instances describe "${DB_INSTANCE_NAME}"     --project="${PROJECT_ID}" &>/dev/null; then
    log_warn "Instance ${DB_INSTANCE_NAME} already exists"
else
    gcloud sql instances create "${DB_INSTANCE_NAME}"         --database-version=POSTGRES_15         --tier=db-f1-micro         --region="${REGION}"         --project="${PROJECT_ID}"         --storage-type=SSD         --storage-size=10GB         --no-backup         --database-flags=max_connections=100         --quiet

    log_success "Cloud SQL instance created: ${DB_INSTANCE_NAME}"
fi

# ── Create database ────────────────────────────────────────
log_step "Creating HR database"

if gcloud sql databases describe "${DB_NAME}"     --instance="${DB_INSTANCE_NAME}"     --project="${PROJECT_ID}" &>/dev/null; then
    log_warn "Database ${DB_NAME} already exists"
else
    gcloud sql databases create "${DB_NAME}"         --instance="${DB_INSTANCE_NAME}"         --project="${PROJECT_ID}"         --quiet
    log_success "Database created: ${DB_NAME}"
fi

# ── Create DB user ─────────────────────────────────────────
log_step "Creating database user"

gcloud sql users create "${DB_USER}"     --instance="${DB_INSTANCE_NAME}"     --password="${DB_PASSWORD}"     --project="${PROJECT_ID}"     --quiet 2>/dev/null &&     log_success "DB user created: ${DB_USER}" ||     log_warn "DB user may already exist"

# ── Create service account for DB access ──────────────────
log_step "Creating HR DB service account"

HR_DB_SA="hr-db-sa@${PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe "${HR_DB_SA}"     --project="${PROJECT_ID}" &>/dev/null; then
    log_warn "Service account already exists"
else
    gcloud iam service-accounts create "hr-db-sa"         --display-name="HR Database Service Account"         --project="${PROJECT_ID}" --quiet
    log_success "Service account created: ${HR_DB_SA}"
fi

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding "${PROJECT_ID}"     --member="serviceAccount:${HR_DB_SA}"     --role="roles/cloudsql.client"     --quiet --format="none"

# Grant to RAG engine SA too
gcloud projects add-iam-policy-binding "${PROJECT_ID}"     --member="serviceAccount:${RAG_SA}"     --role="roles/cloudsql.client"     --quiet --format="none"

log_success "IAM permissions granted"

# ── Get connection name ────────────────────────────────────
log_step "Getting connection details"

CONNECTION_NAME=$(gcloud sql instances describe "${DB_INSTANCE_NAME}"     --project="${PROJECT_ID}"     --format="value(connectionName)" 2>/dev/null)

log_success "Connection name: ${CONNECTION_NAME}"

# ── Store in Secret Manager ────────────────────────────────
log_step "Storing DB credentials in Secret Manager"

DB_URL="postgresql://${DB_USER}:${DB_PASSWORD}@localhost/${DB_NAME}?host=/cloudsql/${CONNECTION_NAME}"

echo -n "${DB_URL}" | gcloud secrets create "hr-db-url"     --data-file=-     --project="${PROJECT_ID}"     --quiet 2>/dev/null ||     echo -n "${DB_URL}" | gcloud secrets versions add "hr-db-url"     --data-file=-     --project="${PROJECT_ID}"     --quiet

log_success "DB URL stored in Secret Manager: hr-db-url"

echo ""
echo "=================================================="
log_success "HR Database setup complete!"
echo ""
echo "  Instance: ${DB_INSTANCE_NAME}"
echo "  Database: ${DB_NAME}"
echo "  Region: ${REGION}"
echo "  Connection: ${CONNECTION_NAME}"
echo ""
echo "Next step: ./scripts/13_hr_data_load.sh --env=${ENVIRONMENT}"
echo "=================================================="
