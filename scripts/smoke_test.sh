#!/bin/bash
# Smoke test after deployment
URL="https://hr-rag-engine-946703664996.asia-south1.run.app"

echo "Running smoke tests..."

# Test 1: Health check
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "${URL}/_stcore/health")
if [ "$HEALTH" = "200" ]; then
    echo "[OK] Health check passed!"
else
    echo "[FAIL] Health check failed: ${HEALTH}"
    exit 1
fi

# Test 2: App loads
APP=$(curl -s -o /dev/null -w "%{http_code}" "${URL}")
if [ "$APP" = "200" ]; then
    echo "[OK] App loads successfully!"
else
    echo "[FAIL] App failed to load: ${APP}"
    exit 1
fi

echo "All smoke tests passed!"
