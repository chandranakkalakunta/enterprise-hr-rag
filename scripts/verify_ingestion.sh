#!/bin/bash
# ============================================================
# Script: verify_ingestion.sh
# Purpose: Verify documents are properly ingested
# Usage: ./scripts/verify_ingestion.sh --env=dev
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
echo " Ingestion Verification - ${ENVIRONMENT}"
echo "=================================================="

PYTHON="${SCRIPT_DIR}/../venv/bin/python3"

${PYTHON} - << INNEREOF
import sys
sys.path.insert(0, "${SCRIPT_DIR}/../src/ingestion")

from firestore_client import FirestoreClient
from bm25_indexer import BM25Indexer
from google.cloud import storage

print("--- Firestore ---")
fs = FirestoreClient("${PROJECT_ID}")
stats = fs.get_stats()
print(f"Active documents: {stats['active_documents']}")
print(f"Total chunks: {stats['total_chunks']}")
for doc_id in sorted(stats['document_ids']):
    print(f"  OK: {doc_id}")

print("--- BM25 Index ---")
bm25 = BM25Indexer(index_path="/tmp/bm25_index_${ENVIRONMENT}.pkl")
bm25_stats = bm25.get_stats()
print(f"Chunks: {bm25_stats['total_chunks']}")
print(f"Built: {bm25_stats['index_built']}")

print("--- Search Test ---")
results = bm25.search("annual leave days", top_k=3)
print(f"Results for annual leave: {len(results)}")
for r in results:
    print(f"  Score: {r['score']:.3f} | {r['text'][:60]}...")

print("--- GCS ---")
client = storage.Client(project="${PROJECT_ID}")
bucket = client.bucket("${DOCS_BUCKET}")
blobs = list(bucket.list_blobs(prefix="current/"))
print(f"Documents in GCS: {len(blobs)}")
for blob in blobs:
    print(f"  OK: {blob.name}")

print("Verification complete!")
INNEREOF
echo "=================================================="
