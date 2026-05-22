#!/bin/bash
# ============================================================
# Script: 00_prerequisites.sh
# Purpose: Verify all required tools and configuration
# Usage: ./scripts/00_prerequisites.sh
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config/common.env"

echo "=================================================="
echo " Enterprise HR RAG Platform - Prerequisites Check"
echo "=================================================="

ERRORS=0

check_tool() {
    if command -v "$1" &>/dev/null; then
        log_success "$1 found: $($1 --version 2>&1 | head -1)"
    else
        log_warn "$1 NOT found! Install from: $2"
        ERRORS=$((ERRORS + 1))
    fi
}

log_step "Checking required tools"
check_tool "gcloud"  "cloud.google.com/sdk"
check_tool "docker"  "docker.com"
check_tool "python3" "python.org"
check_tool "git"     "git-scm.com"
check_tool "curl"    "pre-installed"
check_tool "jq"      "brew install jq"
check_tool "make"    "pre-installed"

log_step "Checking Python version"
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo $PY_VER | cut -d. -f1)
PY_MINOR=$(echo $PY_VER | cut -d. -f2)
if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
    log_success "Python ${PY_VER} >= 3.11 ✅"
else
    log_warn "Python ${PY_VER} found but >= 3.11 required!"
    ERRORS=$((ERRORS + 1))
fi

log_step "Checking gcloud authentication"
if gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q "@"; then
    ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -1)
    log_success "Authenticated as: ${ACCOUNT}"
else
    log_warn "Not authenticated! Run: gcloud auth login"
    ERRORS=$((ERRORS + 1))
fi

log_step "Checking application default credentials"
if gcloud auth application-default print-access-token &>/dev/null; then
    log_success "Application default credentials OK"
else
    log_warn "Run: gcloud auth application-default login"
    ERRORS=$((ERRORS + 1))
fi

log_step "Checking Docker daemon"
if docker info &>/dev/null; then
    log_success "Docker daemon running"
else
    log_warn "Docker not running! Start Docker Desktop"
    ERRORS=$((ERRORS + 1))
fi

log_step "Checking config files"
for f in config/common.env config/dev.env config/prod.env; do
    if [ -f "${SCRIPT_DIR}/../${f}" ]; then
        log_success "Found: ${f}"
    else
        log_warn "Missing: ${f}"
        ERRORS=$((ERRORS + 1))
    fi
done

log_step "Checking API keys"
if [ -n "${GEMINI_API_KEY:-}" ]; then
    log_success "GEMINI_API_KEY is set"
else
    log_warn "GEMINI_API_KEY not set! Run: export GEMINI_API_KEY='your-key'"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "=================================================="
if [ $ERRORS -eq 0 ]; then
    log_success "All prerequisites satisfied! Ready to proceed! 🚀"
    exit 0
else
    echo -e "${RED}Found ${ERRORS} issue(s). Fix them before proceeding!${NC}"
    exit 1
fi
