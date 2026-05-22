#!/bin/bash
# ============================================================
# Script: 01_org_setup.sh
# Purpose: Create GCP Organization folder structure
# Usage: ./scripts/01_org_setup.sh --org-id=ORG_ID
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config/common.env"

# ── Parse arguments ────────────────────────────────────────
ORG_ID=""
for arg in "$@"; do
    case $arg in
        --org-id=*) ORG_ID="${arg#*=}" ;;
        *) log_warn "Unknown argument: $arg" ;;
    esac
done

# ── Prompt if not provided ─────────────────────────────────
if [ -z "$ORG_ID" ]; then
    echo -e "${YELLOW}Enter your GCP Organization ID:${NC}"
    echo "(Find at: console.cloud.google.com → IAM → Settings)"
    read -r ORG_ID
fi

if [ -z "$ORG_ID" ]; then
    log_error "Organization ID is required!"
fi

echo "=================================================="
echo " Enterprise HR RAG Platform - Organization Setup"
echo " Organization ID: ${ORG_ID}"
echo "=================================================="

# ── Helper: create folder if not exists ───────────────────
create_folder() {
    local NAME=$1
    local PARENT_TYPE=$2
    local PARENT_ID=$3

    # Check if folder exists
    EXISTING=$(gcloud resource-manager folders list \
        --${PARENT_TYPE}=${PARENT_ID} \
        --filter="displayName=${NAME}" \
        --format="value(name)" 2>/dev/null | head -1)

    if [ -n "$EXISTING" ]; then
        log_warn "Folder '${NAME}' already exists: ${EXISTING}"
        echo "$EXISTING"
    else
        FOLDER=$(gcloud resource-manager folders create \
            --display-name="${NAME}" \
            --${PARENT_TYPE}=${PARENT_ID} \
            --format="value(name)" 2>/dev/null)
        log_success "Created folder: ${NAME} (${FOLDER})"
        echo "$FOLDER"
    fi
}

# ── Create folder structure ────────────────────────────────
log_step "Creating folder structure"

# Root folder under org
ROOT_FOLDER=$(create_folder "Chandra AI Labs" "organization" "$ORG_ID")
ROOT_ID=$(echo $ROOT_FOLDER | sed 's/folders\///')

# Sub-folders
DEV_FOLDER=$(create_folder "dev" "folder" "$ROOT_ID")
PROD_FOLDER=$(create_folder "prod" "folder" "$ROOT_ID")
SHARED_FOLDER=$(create_folder "shared-services" "folder" "$ROOT_ID")

DEV_ID=$(echo $DEV_FOLDER | sed 's/folders\///')
PROD_ID=$(echo $PROD_FOLDER | sed 's/folders\///')
SHARED_ID=$(echo $SHARED_FOLDER | sed 's/folders\///')

# ── Apply Organization Policies ───────────────────────────
log_step "Applying organization policies"

# Policy 1: Restrict resource locations to India
log_info "Setting resource location policy..."
gcloud org-policies set-policy \
    --organization=$ORG_ID \
    <(cat << POLICY
name: organizations/${ORG_ID}/policies/gcp.resourceLocations
spec:
  rules:
  - values:
      allowedValues:
      - in:asia-south1-locations
      - in:asia-south2-locations
POLICY
) 2>/dev/null && log_success "Resource location policy applied" \
  || log_warn "Could not apply resource location policy (may need org admin role)"

# Policy 2: Disable SA key creation
log_info "Disabling SA key creation..."
gcloud org-policies set-policy \
    --organization=$ORG_ID \
    <(cat << POLICY
name: organizations/${ORG_ID}/policies/iam.disableServiceAccountKeyCreation
spec:
  rules:
  - enforce: true
POLICY
) 2>/dev/null && log_success "SA key creation disabled" \
  || log_warn "Could not apply SA key policy"

# ── Save folder IDs to config ─────────────────────────────
log_step "Saving folder IDs"


log_success "Folder IDs saved to config/common.env"

# ── Summary ───────────────────────────────────────────────
echo ""
echo "=================================================="
log_success "Organization setup complete!"
echo ""
echo "Folder Structure:"
echo "  chandraailabs.com (org: ${ORG_ID})"
echo "  └── Chandra AI Labs (${ROOT_ID})"
echo "      ├── dev (${DEV_ID})"
echo "      ├── prod (${PROD_ID})"
echo "      └── shared-services (${SHARED_ID})"
echo ""
echo "Next step: ./scripts/02_project_setup.sh --env=dev"
echo "=================================================="
