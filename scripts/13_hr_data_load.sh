#!/bin/bash
# ============================================================
# Script: 13_hr_data_load.sh
# Purpose: Generate and load sample HR data for ChandraAILabs
# Usage: ./scripts/13_hr_data_load.sh --env=dev
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
echo " ChandraAILabs HR RAG - HR Data Load"
echo " Environment: ${ENVIRONMENT}"
echo " Project: ${PROJECT_ID}"
echo "=================================================="

PYTHON="${SCRIPT_DIR}/../venv/bin/python3"

# Check DB is ready
log_step "Checking Cloud SQL instance status"
for attempt in $(seq 1 20); do
    STATE=$(gcloud sql instances describe "${DB_INSTANCE_NAME}"         --project="${PROJECT_ID}"         --format="value(state)" 2>/dev/null)
    if [ "${STATE}" = "RUNNABLE" ]; then
        log_success "Instance is RUNNABLE!"
        break
    fi
    log_info "Attempt ${attempt}/20 - State: ${STATE} (30s wait)"
    sleep 30
done

# Install dependencies
log_step "Installing DB packages"
"${PYTHON}" -m pip install     "cloud-sql-python-connector[pg8000]"     pg8000 sqlalchemy --quiet
log_success "Packages installed!"

# Run Python data loader
log_step "Creating schema and loading data"
"${PYTHON}" "${SCRIPT_DIR}/../src/database/load_hr_data.py"     --project="${PROJECT_ID}"     --instance="${DB_INSTANCE_NAME}"     --db="${DB_NAME}"     --user="${DB_USER}"     --password="${DB_PASSWORD}"     --region="${REGION}"

echo ""
echo "=================================================="
log_success "HR data loaded!"
echo "Next: ./scripts/14_personal_rag.sh --env=${ENVIRONMENT}"
echo "=================================================="
