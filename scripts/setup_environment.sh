#!/bin/bash
# ============================================================
# Script: setup_environment.sh
# Purpose: Setup Python virtual environment with all deps
# Usage: ./scripts/setup_environment.sh
# Run this ONCE after cloning the repository!
# ============================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/.."

source "${SCRIPT_DIR}/../config/common.env"

echo "=================================================="
echo " Enterprise HR RAG Platform - Environment Setup"
echo "=================================================="

# ── Check Python version ───────────────────────────────────
log_step "Checking Python version"
PYTHON_VERSION=$(python3 --version 2>&1 | awk "{print \$2}")
REQUIRED="3.11"

if python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)"; then
    log_success "Python ${PYTHON_VERSION} >= 3.11"
else
    log_error "Python >= 3.11 required! Found: ${PYTHON_VERSION}"
fi

# ── Create virtual environment ─────────────────────────────
log_step "Creating virtual environment"

if [ -d "${PROJECT_DIR}/venv" ]; then
    log_warn "venv already exists - recreating..."
    rm -rf "${PROJECT_DIR}/venv"
fi

python3 -m venv "${PROJECT_DIR}/venv"
log_success "Virtual environment created!"

# ── Activate and install packages ─────────────────────────
log_step "Installing Python packages"

source "${PROJECT_DIR}/venv/bin/activate"

# Upgrade pip first
pip install --upgrade pip --quiet

# Install all requirements
pip install -r "${PROJECT_DIR}/requirements.txt" --quiet

log_success "All packages installed!"

# ── Verify key packages ────────────────────────────────────
log_step "Verifying installations"

python3 -c "import streamlit; print(f'  streamlit: {streamlit.__version__}')"
python3 -c "from google import genai; print(f'  google-genai: OK')"
python3 -c "from google.cloud import firestore; print(f'  firestore: OK')"
python3 -c "from google.cloud import storage; print(f'  storage: OK')"
python3 -c "from rank_bm25 import BM25Okapi; print(f'  rank-bm25: OK')"

log_success "All packages verified!"

# ── Create .env file for local development ─────────────────
log_step "Creating local .env file"

if [ ! -f "${PROJECT_DIR}/.env" ]; then
    cat > "${PROJECT_DIR}/.env" << ENVEOF
# Local Development Environment Variables
# DO NOT COMMIT THIS FILE!
GEMINI_API_KEY=your-gemini-api-key-here
PROJECT_ID=hr-rag-dev
REGION=asia-south1
ENVIRONMENT=dev
DOCS_BUCKET=hr-rag-dev-documents
VECTOR_ENDPOINT_ID=projects/946703664996/locations/asia-south1/indexEndpoints/2379105667995664384
DEPLOYED_INDEX_ID=hr_rag_deployed_index
ENVEOF
    log_success ".env file created - update with your API keys!"
else
    log_warn ".env already exists - skipping"
fi

echo ""
echo "=================================================="
log_success "Environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your API keys"
echo "2. Activate venv: source venv/bin/activate"
echo "3. Run ingestion: ./scripts/ingest_documents.sh --env=dev"
echo "4. Start UI: streamlit run src/ui/app.py"
echo "=================================================="
