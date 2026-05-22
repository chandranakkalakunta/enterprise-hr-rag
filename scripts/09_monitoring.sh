#!/bin/bash
# ============================================================
# Script: 09_monitoring.sh
# Purpose: Create monitoring dashboards and alert policies
# Usage: ./scripts/09_monitoring.sh --env=dev
# ============================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config/common.env"

ENVIRONMENT=""
ALERT_EMAIL=""

for arg in "$@"; do
    case $arg in
        --env=*)   ENVIRONMENT="${arg#*=}" ;;
        --email=*) ALERT_EMAIL="${arg#*=}" ;;
    esac
done

if [ -z "$ENVIRONMENT" ]; then
    echo -e "${YELLOW}Enter environment (dev/prod):${NC}"
    read -r ENVIRONMENT
fi

if [ -z "$ALERT_EMAIL" ]; then
    echo -e "${YELLOW}Enter alert email address:${NC}"
    read -r ALERT_EMAIL
fi

source "${SCRIPT_DIR}/../config/${ENVIRONMENT}.env"

echo "=================================================="
echo " Enterprise HR RAG Platform - Monitoring Setup"
echo " Environment: ${ENVIRONMENT}"
echo " Project: ${PROJECT_ID}"
echo "=================================================="

# ── Create notification channel ────────────────────────────
log_step "Creating email notification channel"

CHANNEL_ID=$(gcloud alpha monitoring channels create \
    --project="${PROJECT_ID}" \
    --display-name="HR RAG Alerts" \
    --type=email \
    --channel-labels="email_address=${ALERT_EMAIL}" \
    --format="value(name)" 2>/dev/null)

if [ -z "$CHANNEL_ID" ]; then
    log_warn "Could not create notification channel"
    CHANNEL_ID=""
else
    log_success "Notification channel created: ${ALERT_EMAIL}"
fi

# ── Create uptime check ────────────────────────────────────
log_step "Creating uptime check"

SERVICE_URL=$(gcloud run services describe "${RAG_ENGINE_NAME}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --format="value(status.url)" 2>/dev/null)

if [ -n "${SERVICE_URL}" ]; then
    # Extract hostname
    HOST=$(echo "${SERVICE_URL}" | sed 's|https://||')

    gcloud monitoring uptime create "hr-rag-uptime-${ENVIRONMENT}" \
        --project="${PROJECT_ID}" \
        --resource-type=uptime-url \
        --resource-labels="host=${HOST},project_id=${PROJECT_ID}" \
        --check-interval=300 \
        --timeout=10 \
        --regions=asia-pacific \
        --quiet 2>/dev/null && \
        log_success "Uptime check created (5 min interval)" || \
        log_warn "Uptime check may already exist"
else
    log_warn "Service URL not found - deploy RAG engine first!"
fi

# ── Create alert policies ──────────────────────────────────
log_step "Creating alert policies"

# Alert 1: High error rate
ALERT_FILE=$(mktemp /tmp/alert-XXXXXX.json)
cat > "${ALERT_FILE}" << ALERTEOF
{
  "displayName": "HR RAG High Error Rate - ${ENVIRONMENT}",
  "conditions": [{
    "displayName": "Error rate > 5%",
    "conditionThreshold": {
      "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${RAG_ENGINE_NAME}\" AND metric.type=\"run.googleapis.com/request_count\"",
      "aggregations": [{
        "alignmentPeriod": "300s",
        "perSeriesAligner": "ALIGN_RATE"
      }],
      "comparison": "COMPARISON_GT",
      "thresholdValue": 0.05,
      "duration": "300s"
    }
  }],
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
ALERTEOF

gcloud alpha monitoring policies create \
    --project="${PROJECT_ID}" \
    --policy-from-file="${ALERT_FILE}" \
    --quiet 2>/dev/null && \
    log_success "Error rate alert created" || \
    log_warn "Error rate alert may already exist"
rm -f "${ALERT_FILE}"

# Alert 2: High latency
ALERT_FILE=$(mktemp /tmp/alert-XXXXXX.json)
cat > "${ALERT_FILE}" << ALERTEOF
{
  "displayName": "HR RAG High Latency - ${ENVIRONMENT}",
  "conditions": [{
    "displayName": "p99 latency > 5s",
    "conditionThreshold": {
      "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${RAG_ENGINE_NAME}\" AND metric.type=\"run.googleapis.com/request_latencies\"",
      "aggregations": [{
        "alignmentPeriod": "300s",
        "perSeriesAligner": "ALIGN_PERCENTILE_99"
      }],
      "comparison": "COMPARISON_GT",
      "thresholdValue": 5000,
      "duration": "300s"
    }
  }]
}
ALERTEOF

gcloud alpha monitoring policies create \
    --project="${PROJECT_ID}" \
    --policy-from-file="${ALERT_FILE}" \
    --quiet 2>/dev/null && \
    log_success "Latency alert created" || \
    log_warn "Latency alert may already exist"
rm -f "${ALERT_FILE}"

echo ""
echo "=================================================="
log_success "Monitoring setup complete!"
echo ""
echo "  Uptime Check: 5-minute intervals"
echo "  Alert: Error rate > 5%"
echo "  Alert: Latency p99 > 5s"
echo "  Notifications: ${ALERT_EMAIL}"
echo ""
echo "View dashboards:"
echo "  https://console.cloud.google.com/monitoring?project=${PROJECT_ID}"
echo ""
echo "Next step: ./scripts/10_evaluation.sh --env=${ENVIRONMENT}"
echo "=================================================="
