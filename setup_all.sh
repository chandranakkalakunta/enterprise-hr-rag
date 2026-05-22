#!/bin/bash
# ============================================================
# setup_all.sh — Master Setup Script
# Purpose: Run ALL setup scripts in sequence
# Usage: ./setup_all.sh --env=dev
#        ./setup_all.sh --env=prod
# ============================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config/common.env"

# ── Parse arguments ────────────────────────────────────────
ENVIRONMENT=""
SKIP_ORG=false
START_FROM=0

for arg in "$@"; do
    case $arg in
        --env=*)        ENVIRONMENT="${arg#*=}" ;;
        --skip-org)     SKIP_ORG=true ;;
        --start-from=*) START_FROM="${arg#*=}" ;;
        --help|-h)
            echo "Usage: ./setup_all.sh --env=dev|prod [--skip-org] [--start-from=N]"
            echo ""
            echo "Options:"
            echo "  --env=dev|prod    Environment to setup"
            echo "  --skip-org        Skip organization setup"
            echo "  --start-from=N    Start from script N (0-11)"
            echo ""
            echo "Examples:"
            echo "  ./setup_all.sh --env=dev"
            echo "  ./setup_all.sh --env=dev --skip-org"
            echo "  ./setup_all.sh --env=dev --start-from=5"
            exit 0
            ;;
    esac
done

if [ -z "$ENVIRONMENT" ]; then
    echo -e "${YELLOW}Enter environment (dev/prod):${NC}"
    read -r ENVIRONMENT
fi

echo "=========================================================="
echo "  Enterprise HR RAG Platform — Full Setup"
echo "  Environment: ${ENVIRONMENT}"
echo "  Started: $(date)"
echo "=========================================================="
echo ""

# ── Track timing ───────────────────────────────────────────
START_TIME=$(date +%s)

run_script() {
    local STEP=$1
    local SCRIPT=$2
    local DESCRIPTION=$3

    if [ "$STEP" -lt "$START_FROM" ]; then
        log_warn "Skipping Step ${STEP}: ${DESCRIPTION}"
        return 0
    fi

    echo ""
    echo "----------------------------------------------------------"
    log_step "Step ${STEP}: ${DESCRIPTION}"
    echo "----------------------------------------------------------"

    if bash "${SCRIPT_DIR}/scripts/${SCRIPT}" --env="${ENVIRONMENT}"; then
        log_success "Step ${STEP} complete: ${DESCRIPTION}"
    else
        log_error "Step ${STEP} FAILED: ${DESCRIPTION}"
        echo "Fix the error and rerun with: --start-from=${STEP}"
        exit 1
    fi
}

# ── Run all scripts ────────────────────────────────────────
run_script 0  "00_prerequisites.sh"  "Prerequisites Check"

if [ "$SKIP_ORG" = false ]; then
    run_script 1  "01_org_setup.sh"      "Organization Setup"
fi

run_script 2  "02_project_setup.sh"  "Project Creation"
run_script 3  "03_networking.sh"     "Networking Setup"
run_script 4  "04_security.sh"       "Security Setup"
run_script 5  "05_storage.sh"        "Storage Setup"
run_script 6  "06_vector_search.sh"  "Vector Search Setup"
run_script 7  "07_data_pipeline.sh"  "Data Pipeline Setup"
run_script 8  "08_rag_deployment.sh" "RAG Application Deployment"
run_script 9  "09_monitoring.sh"     "Monitoring & Alerting"
run_script 10 "10_evaluation.sh"     "RAGAS Evaluation Setup"
run_script 11 "11_cicd.sh"           "CI/CD Pipeline"

# ── Calculate time ─────────────────────────────────────────
END_TIME=$(date +%s)
DURATION=$(( (END_TIME - START_TIME) / 60 ))

echo ""
echo "=========================================================="
log_success "Enterprise HR RAG Platform setup complete!"
echo ""
echo "  Environment: ${ENVIRONMENT}"
echo "  Duration: ${DURATION} minutes"
echo "  Completed: $(date)"
echo ""
echo "  Next steps:"
echo "  1. Wait for Vector Search index (20-30 min)"
echo "     Check: gcloud ai indexes list --region=${REGION} --project=${PROJECT_ID}"
echo "  2. Deploy index: ./scripts/06b_deploy_index.sh --env=${ENVIRONMENT}"
echo "  3. Upload documents: ./scripts/upload_documents.sh --env=${ENVIRONMENT}"
echo "  4. Run evaluation: make evaluate"
echo "=========================================================="
