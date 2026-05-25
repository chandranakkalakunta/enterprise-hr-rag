#!/bin/bash
# ============================================================
# Script: 01_org_setup.sh
# Purpose: Setup GCP Organization folder structure and policies
# Usage: ./scripts/01_org_setup.sh
# ============================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config/common.env"

echo "=================================================="
echo " Enterprise HR RAG - Organization Setup"
echo " Organization: chandra-idle-org"
echo " Org ID: ${ORG_ID}"
echo "=================================================="

# ── Helper: create folder if not exists ───────────────────
create_folder() {
    local NAME=$1
    local PARENT_TYPE=$2
    local PARENT_ID=$3

    EXISTING=$(gcloud resource-manager folders list         --"${PARENT_TYPE}"="${PARENT_ID}"         --filter="displayName=${NAME}"         --format="value(name)" 2>/dev/null | head -1)

    if [ -n "$EXISTING" ]; then
        log_warn "Folder already exists: ${NAME}"
        echo "$EXISTING"
    else
        FOLDER=$(gcloud resource-manager folders create             --display-name="${NAME}"             --"${PARENT_TYPE}"="${PARENT_ID}"             --format="value(name)" 2>/dev/null)
        log_success "Created folder: ${NAME}"
        echo "$FOLDER"
    fi
}

# ── Create folder structure ────────────────────────────────
log_step "Creating GCP folder structure"

NON_PROD=$(create_folder "Non-Production" "organization" "${ORG_ID}")
NON_PROD_ID=$(echo "${NON_PROD}" | grep -o "[0-9]*$")

PROD=$(create_folder "Production" "organization" "${ORG_ID}")
PROD_ID=$(echo "${PROD}" | grep -o "[0-9]*$")

log_info "Non-Production ID: ${NON_PROD_ID}"
log_info "Production ID: ${PROD_ID}"

# ── Move project to Non-Production ────────────────────────
log_step "Placing ${PROJECT_ID} in Non-Production folder"

CURRENT_PARENT=$(gcloud projects describe "${PROJECT_ID}"     --format="value(parent.id)" 2>/dev/null)

if [ "${CURRENT_PARENT}" = "${NON_PROD_ID}" ]; then
    log_warn "Project already in Non-Production folder"
else
    echo "y" | gcloud beta projects move "${PROJECT_ID}"         --folder="${NON_PROD_ID}" 2>/dev/null &&         log_success "Project moved to Non-Production!" ||         log_warn "Could not move project"
fi

# ── Apply org policies ─────────────────────────────────────
log_step "Applying organization policies"

# Policy 1: Restrict resources to India only (Data Sovereignty)
cat > /tmp/location_policy.yaml << YAMLEOF
name: organizations/${ORG_ID}/policies/gcp.resourceLocations
spec:
  rules:
  - values:
      allowedValues:
      - in:asia-south1-locations
YAMLEOF

gcloud org-policies set-policy /tmp/location_policy.yaml 2>/dev/null &&     log_success "Policy 1: Resources restricted to asia-south1 (India)" ||     log_warn "Policy 1: Could not set location policy"

# Policy 2: Disable Service Account key creation
# Forces use of Workload Identity - more secure!
cat > /tmp/sa_key_policy.yaml << YAMLEOF
name: organizations/${ORG_ID}/policies/iam.disableServiceAccountKeyCreation
spec:
  rules:
  - enforce: true
YAMLEOF

gcloud org-policies set-policy /tmp/sa_key_policy.yaml 2>/dev/null &&     log_success "Policy 2: SA key creation disabled (use Workload Identity)" ||     log_warn "Policy 2: Could not set SA key policy"

# Policy 3: Enforce uniform bucket-level IAM on GCS
cat > /tmp/bucket_policy.yaml << YAMLEOF
name: organizations/${ORG_ID}/policies/storage.uniformBucketLevelAccess
spec:
  rules:
  - enforce: true
YAMLEOF

gcloud org-policies set-policy /tmp/bucket_policy.yaml 2>/dev/null &&     log_success "Policy 3: Uniform bucket IAM enforced on GCS" ||     log_warn "Policy 3: Could not set bucket policy"

# Policy 4: Disable default service account
cat > /tmp/default_sa_policy.yaml << YAMLEOF
name: organizations/${ORG_ID}/policies/iam.automaticIamGrantsForDefaultServiceAccounts
spec:
  rules:
  - enforce: false
YAMLEOF

gcloud org-policies set-policy /tmp/default_sa_policy.yaml 2>/dev/null &&     log_success "Policy 4: Default SA auto-grants disabled" ||     log_warn "Policy 4: Could not set default SA policy"

# Cleanup temp files
rm -f /tmp/location_policy.yaml /tmp/sa_key_policy.yaml       /tmp/bucket_policy.yaml /tmp/default_sa_policy.yaml

echo ""
echo "=================================================="
log_success "Organization setup complete!"
echo ""
echo "Structure:"
echo "  chandra-idle-org (${ORG_ID})"
echo "  ├── Non-Production (${NON_PROD_ID})"
echo "  │   └── ${PROJECT_ID} (dev)"
echo "  └── Production (${PROD_ID})"
echo "      └── hr-rag-prod (future)"
echo ""
echo "Org Policies Applied:"
echo "  1. Resources: asia-south1 only (India data sovereignty)"
echo "  2. SA Keys: disabled (use Workload Identity)"
echo "  3. GCS: uniform bucket IAM enforced"
echo "  4. Default SA: auto-grants disabled"
echo ""
echo "Next step: ./scripts/02_project_setup.sh --env=dev"
echo "=================================================="
