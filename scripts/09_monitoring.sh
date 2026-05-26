#!/bin/bash
# ============================================================
# Script: 09_monitoring.sh
# Purpose: Create monitoring dashboards and alert policies
# Usage: ./scripts/09_monitoring.sh --env=dev --email=you@example.com
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

[ -z "$ENVIRONMENT" ] && { echo -e "${YELLOW}Enter environment (dev/prod):${NC}"; read -r ENVIRONMENT; }
[ -z "$ALERT_EMAIL" ]  && { echo -e "${YELLOW}Enter alert email address:${NC}";  read -r ALERT_EMAIL;  }

source "${SCRIPT_DIR}/../config/${ENVIRONMENT}.env"

SERVICE_NAME="${RAG_ENGINE_NAME}"

echo "=================================================="
echo " Enterprise HR RAG Platform — Monitoring Setup"
echo " Environment : ${ENVIRONMENT}"
echo " Project     : ${PROJECT_ID}"
echo " Service     : ${SERVICE_NAME}"
echo " Alert email : ${ALERT_EMAIL}"
echo "=================================================="

# ── Notification channel ──────────────────────────────────
log_step "Creating email notification channel"

CHANNEL_ID=$(gcloud alpha monitoring channels create \
    --project="${PROJECT_ID}" \
    --display-name="HR RAG Alerts — ${ENVIRONMENT}" \
    --type=email \
    --channel-labels="email_address=${ALERT_EMAIL}" \
    --format="value(name)" 2>/dev/null || true)

if [ -z "${CHANNEL_ID:-}" ]; then
    # Channel may already exist — look it up
    CHANNEL_ID=$(gcloud alpha monitoring channels list \
        --project="${PROJECT_ID}" \
        --filter="displayName='HR RAG Alerts — ${ENVIRONMENT}'" \
        --format="value(name)" 2>/dev/null | head -1 || true)
fi

if [ -n "${CHANNEL_ID:-}" ]; then
    log_success "Notification channel: ${CHANNEL_ID}"
else
    log_warn "Could not create/find notification channel — alerts will fire without email"
    CHANNEL_ID=""
fi

# Build notificationChannels JSON fragment (empty array if no channel)
if [ -n "${CHANNEL_ID:-}" ]; then
    NOTIF_JSON="\"notificationChannels\": [\"${CHANNEL_ID}\"],"
else
    NOTIF_JSON="\"notificationChannels\": [],"
fi

# ── Uptime check ──────────────────────────────────────────
log_step "Creating uptime check"

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --format="value(status.url)" 2>/dev/null || true)

if [ -n "${SERVICE_URL:-}" ]; then
    HOST=$(echo "${SERVICE_URL}" | sed 's|https://||')
    gcloud monitoring uptime create "hr-rag-uptime-${ENVIRONMENT}" \
        --project="${PROJECT_ID}" \
        --resource-type=uptime-url \
        --resource-labels="host=${HOST},project_id=${PROJECT_ID}" \
        --check-interval=300 \
        --timeout=10 \
        --regions=asia-pacific \
        --quiet 2>/dev/null && \
        log_success "Uptime check created (5-min interval, ${HOST})" || \
        log_warn "Uptime check may already exist"
else
    log_warn "Service URL not found — deploy the RAG engine first"
fi

# ── Alert policies ────────────────────────────────────────
log_step "Creating alert policies"

_create_alert() {
    local file="$1" label="$2"
    gcloud alpha monitoring policies create \
        --project="${PROJECT_ID}" \
        --policy-from-file="${file}" \
        --quiet 2>/dev/null && \
        log_success "${label} alert created" || \
        log_warn "${label} alert may already exist"
    rm -f "${file}"
}

# Alert 1: High 5xx error rate
A=$(mktemp /tmp/alert-XXXXXX.json)
cat > "${A}" << EOF
{
  "displayName": "HR RAG — High 5xx Error Rate (${ENVIRONMENT})",
  ${NOTIF_JSON}
  "conditions": [{
    "displayName": "5xx responses > 5 % of traffic for 5 min",
    "conditionThreshold": {
      "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\"",
      "aggregations": [{
        "alignmentPeriod": "300s",
        "perSeriesAligner": "ALIGN_RATE",
        "crossSeriesReducer": "REDUCE_SUM",
        "groupByFields": ["resource.labels.service_name"]
      }],
      "comparison": "COMPARISON_GT",
      "thresholdValue": 0.05,
      "duration": "300s"
    }
  }],
  "alertStrategy": { "autoClose": "1800s" }
}
EOF
_create_alert "${A}" "High error rate"

# Alert 2: High p99 latency
A=$(mktemp /tmp/alert-XXXXXX.json)
cat > "${A}" << EOF
{
  "displayName": "HR RAG — High Latency p99 > 5 s (${ENVIRONMENT})",
  ${NOTIF_JSON}
  "conditions": [{
    "displayName": "p99 request latency > 5 000 ms",
    "conditionThreshold": {
      "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_latencies\"",
      "aggregations": [{
        "alignmentPeriod": "300s",
        "perSeriesAligner": "ALIGN_PERCENTILE_99",
        "crossSeriesReducer": "REDUCE_PERCENTILE_99",
        "groupByFields": ["resource.labels.service_name"]
      }],
      "comparison": "COMPARISON_GT",
      "thresholdValue": 5000,
      "duration": "300s"
    }
  }],
  "alertStrategy": { "autoClose": "1800s" }
}
EOF
_create_alert "${A}" "High latency"

# Alert 3: No requests (service down / cold-start death)
A=$(mktemp /tmp/alert-XXXXXX.json)
cat > "${A}" << EOF
{
  "displayName": "HR RAG — Service Appears Down (${ENVIRONMENT})",
  ${NOTIF_JSON}
  "conditions": [{
    "displayName": "Zero active instances for 10 min",
    "conditionThreshold": {
      "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/container/instance_count\" AND metric.labels.state=\"active\"",
      "aggregations": [{
        "alignmentPeriod": "600s",
        "perSeriesAligner": "ALIGN_MAX",
        "crossSeriesReducer": "REDUCE_MAX",
        "groupByFields": ["resource.labels.service_name"]
      }],
      "comparison": "COMPARISON_LT",
      "thresholdValue": 1,
      "duration": "600s"
    }
  }],
  "alertStrategy": { "autoClose": "3600s" }
}
EOF
_create_alert "${A}" "Service down"

# Alert 4: High memory utilisation
A=$(mktemp /tmp/alert-XXXXXX.json)
cat > "${A}" << EOF
{
  "displayName": "HR RAG — High Memory Utilisation > 85 % (${ENVIRONMENT})",
  ${NOTIF_JSON}
  "conditions": [{
    "displayName": "Container memory utilisation > 85 %",
    "conditionThreshold": {
      "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/container/memory/utilizations\"",
      "aggregations": [{
        "alignmentPeriod": "300s",
        "perSeriesAligner": "ALIGN_PERCENTILE_99",
        "crossSeriesReducer": "REDUCE_MEAN",
        "groupByFields": ["resource.labels.service_name"]
      }],
      "comparison": "COMPARISON_GT",
      "thresholdValue": 0.85,
      "duration": "300s"
    }
  }],
  "alertStrategy": { "autoClose": "1800s" }
}
EOF
_create_alert "${A}" "High memory"

# ── Dashboard ─────────────────────────────────────────────
log_step "Creating Cloud Monitoring dashboard"

DASHBOARD_TEMPLATE="${SCRIPT_DIR}/../monitoring/dashboard.json"
DASHBOARD_FILE=$(mktemp /tmp/dashboard-XXXXXX.json)

# Substitute placeholders in template
sed \
    -e "s|\${ENVIRONMENT}|${ENVIRONMENT}|g" \
    -e "s|\${SERVICE_NAME}|${SERVICE_NAME}|g" \
    -e "s|\${PROJECT_ID}|${PROJECT_ID}|g" \
    "${DASHBOARD_TEMPLATE}" > "${DASHBOARD_FILE}"

gcloud monitoring dashboards create \
    --project="${PROJECT_ID}" \
    --config-from-file="${DASHBOARD_FILE}" \
    --quiet 2>/dev/null && \
    log_success "Dashboard 'HR RAG Platform — ${ENVIRONMENT}' created" || \
    log_warn "Dashboard may already exist (update it manually in Cloud Console)"
rm -f "${DASHBOARD_FILE}"

# ── Summary ───────────────────────────────────────────────
echo ""
echo "=================================================="
log_success "Monitoring setup complete!"
echo ""
echo "  Uptime check  : 5-min intervals, asia-pacific probe"
echo "  Alert         : 5xx error rate  > 5 %  (→ ${ALERT_EMAIL})"
echo "  Alert         : Latency p99     > 5 s   (→ ${ALERT_EMAIL})"
echo "  Alert         : Service down    10 min  (→ ${ALERT_EMAIL})"
echo "  Alert         : Memory          > 85 %  (→ ${ALERT_EMAIL})"
echo "  Dashboard     : HR RAG Platform — ${ENVIRONMENT}"
echo ""
echo "View in Cloud Console:"
echo "  https://console.cloud.google.com/monitoring/dashboards?project=${PROJECT_ID}"
echo "  https://console.cloud.google.com/monitoring/alerting?project=${PROJECT_ID}"
echo ""
echo "Next step: ./scripts/10_evaluation.sh --env=${ENVIRONMENT}"
echo "=================================================="
