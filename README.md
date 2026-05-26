# Enterprise HR RAG Platform

> Reference-grade Enterprise RAG on Google Cloud Platform

A production-ready HR Policy Q&A system built with hybrid RAG architecture,
enterprise security, personal data integration, privacy-compliant analytics,
and operational monitoring.

Live Demo: https://hr-rag-engine-946703664996.asia-south1.run.app

Demo Login:
- Email: demo@chandraailabs.com | Password: demo123
- Email: guest@chandraailabs.com | Password: guest123

---

## What It Does

Employees ask natural language questions and get accurate, personalized answers.

| Question | Type | Source |
|----------|------|--------|
| How many leaves do I have? | Personal | HR Database |
| What is my CTC? | Personal | HR Database |
| What is my performance rating? | Personal | HR Database |
| What is the WFH policy? | Policy | HR Documents |
| Am I eligible for WFH? | Hybrid | DB + Policy |
| How do I apply for leave? | Policy | HR Documents |

---

## Architecture

```
Employee Login (Google OAuth)
          |
          v
    Query Router (Intent Detection)
     /         |          \
Personal     Policy      Hybrid
   |            |           |
Cloud SQL    BM25 +       Both
HR DB       Vector      Combined
   \          Search       /
    \           |         /
     \          v        /
      Gemini 2.5 Flash
              |
              v
    Personalized Answer + Citations
              |
              v
    BigQuery Analytics (No PII!)
              |
              v
    Cloud Monitoring Dashboard
```

---

## Security Architecture

| Layer | Implementation |
|-------|---------------|
| Authentication | Google OAuth (company email) |
| Container Security | Binary Authorization + KMS RSA-4096 |
| Secret Management | Google Cloud Secret Manager |
| Identity | 4 dedicated Service Accounts (least privilege) |
| Encryption | CMEK with Cloud KMS |
| Network | VPC with private subnets + Cloud NAT |
| Audit | Cloud Logging (structured JSON) + BigQuery (PII-free) |

---

## Privacy & Compliance

| Requirement | Implementation |
|-------------|---------------|
| GDPR Article 5 | Data minimization - no PII in logs |
| India DPDP Act 2023 | Anonymized analytics |
| No PII in BigQuery | hashed_user_id, question_category only |
| No answer text logged | Only metadata stored |
| Right to erasure | Firestore TTL + partitioned BQ |

BigQuery stores ONLY:
- hashed_user_id (irreversible SHA-256)
- question_category (leave/wfh/ctc/policy)
- intent (personal/policy/hybrid)
- department (Engineering/HR etc)
- latency_ms, model_used, success, timestamp

BigQuery NEVER stores:
- Employee name or email
- Actual question text
- Actual answer text
- CTC, leave balance, ratings

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Gemini 2.5 Flash |
| Embeddings | gemini-embedding-001 (3072 dims) |
| Dense Retrieval | Vertex AI Vector Search (STREAM_UPDATE) |
| Sparse Retrieval | BM25 (rank-bm25) |
| Hybrid Fusion | Reciprocal Rank Fusion (RRF) |
| Response Cache | In-memory TTL cache (30 min) |
| Personal Data | Cloud SQL PostgreSQL |
| Metadata Store | Google Firestore |
| Analytics | BigQuery (anonymized) |
| Document Store | Google Cloud Storage |
| UI | Streamlit |
| Auth | Google OAuth |
| Deployment | Google Cloud Run |
| Security | Binary Authorization + KMS |
| Monitoring | Cloud Monitoring + Cloud Logging (structured JSON) |
| IaC | 14 Shell Scripts + Makefile |

---

## Monitoring

Operational monitoring is implemented at two layers:

### App Layer (`src/monitoring/`)
- **Structured JSON logging** — every log line is a Cloud Logging-compatible JSON object with `severity`, `message`, `timestamp`, and structured fields (intent, latency_ms, success). Parsed automatically by Cloud Run → Cloud Logging.
- **Per-query telemetry** — each query logs intent, latency_ms, chunks_retrieved, success/failure to both Cloud Logging and BigQuery.

### GCP Layer
- **Cloud Monitoring Dashboard** — 8 widgets: request rate, latency p50/p95/p99, error rate (4xx/5xx), CPU utilisation, memory utilisation, active instances, error log panel.
- **4 Alert Policies** (all wired to email):
  - 5xx error rate > 5% for 5 min
  - Latency p99 > 5s for 5 min
  - Service down (zero active instances for 10 min)
  - Memory utilisation > 85% for 5 min
- **Uptime check** — 5-minute interval from asia-pacific probe

View dashboards:
```
https://console.cloud.google.com/monitoring/dashboards?project=hr-rag-dev
https://console.cloud.google.com/monitoring/alerting?project=hr-rag-dev
```

Run monitoring setup:
```bash
./scripts/09_monitoring.sh --env=dev --email=you@example.com
```

---

## Response Caching

Policy queries are cached in-memory per Cloud Run instance (TTL: 30 minutes):

- **Cache miss** — full retrieval + Gemini generation; result stored in cache
- **Cache hit** — answer returned instantly; BigQuery logs `latency_ms=0`, `model_used=cache`
- **Cache size** — capped at 100 entries (LRU eviction)
- **Invalidation** — automatic on TTL expiry or container restart; manual via `engine.invalidate_cache()`

Personal and hybrid queries are not cached (data changes per employee).

---

## Evaluation Results

| Metric | BM25 Only | Hybrid RAG | Latest (2026-05-26) |
|--------|-----------|------------|---------------------|
| Avg Relevancy | 0.635 | 0.674 | **0.863** |
| Source Accuracy | 1.000 | 1.000 | **0.967** |
| Easy Questions | 0.706 | 0.740 | **0.850** |
| Medium Questions | 0.611 | 0.630 | **0.910** |
| Hard Questions | 0.377 | 0.522 | **0.830** |

60 questions · Model: gemini-2.5-flash · chunk_size: 1024 · alpha: 0.2

---

## Analytics Insights (Live Data)

> Aggregated from BigQuery — updated 2026-05-26

| Intent | Category | Queries | Avg Latency | Cache Hits |
|--------|----------|---------|-------------|------------|
| policy | leave | 209 | 4,351ms | 9 (4%) |
| policy | wfh | 101 | 4,536ms | 3 (3%) |
| policy | performance | 51 | 4,793ms | 1 (2%) |
| policy | travel | 41 | 3,535ms | 0 |
| policy | training | 37 | 4,689ms | 2 (5%) |
| policy | grievance | 34 | 4,378ms | 0 |
| policy | security | 30 | 3,720ms | 1 (3%) |
| hybrid | performance | 30 | 5,400ms | 0 |
| personal | general | 23 | 2,195ms | 0 |
| personal | compensation | 15 | 2,223ms | 0 |

Key observations:
- Personal queries (2–2.2s) are ~2x faster than policy queries (3.5–5.4s) — no vector search needed
- Hybrid queries (5.4s) are slowest — combine DB lookup + retrieval + generation
- Cache hit rate is low due to recent deployments resetting in-memory cache; grows with usage
- Leave and WFH are the most queried categories

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/chandranakkalakunta/enterprise-hr-rag
cd enterprise-hr-rag

# Setup Python environment
make setup-env

# Setup GCP infrastructure (one command!)
./setup_all.sh --env=dev

# Upload documents and ingest
make ingest

# Run evaluation
make evaluate

# Deploy to Cloud Run
make deploy-dev

# Setup monitoring dashboards and alerts
./scripts/09_monitoring.sh --env=dev --email=you@example.com
```

---

## Project Structure

```
enterprise-hr-rag/
├── setup_all.sh              # ONE command setup
├── Makefile                  # Developer commands
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container definition
├── config/                   # Environment configs (dev/prod)
├── monitoring/               # Cloud Monitoring dashboard JSON
├── scripts/                  # IaC scripts 00-14
│   ├── 00_prerequisites.sh
│   ├── 01_org_setup.sh
│   ├── 02_project_setup.sh   # 19 APIs enabled
│   ├── 03_networking.sh      # VPC + subnets + NAT
│   ├── 04_security.sh        # IAM + KMS + Binary Auth
│   ├── 05_storage.sh         # GCS + BigQuery + Firestore
│   ├── 06_vector_search.sh   # Vertex AI Vector Search
│   ├── 07_data_pipeline.sh   # Cloud Functions
│   ├── 08_rag_deployment.sh  # Cloud Run deployment
│   ├── 09_monitoring.sh      # Dashboards + Alerts
│   ├── 10_evaluation.sh      # RAGAS pipeline
│   ├── 11_cicd.sh            # Cloud Build CI/CD
│   ├── 12_hr_database.sh     # Cloud SQL PostgreSQL
│   └── 13_hr_data_load.sh    # Sample employee data
└── src/
    ├── ingestion/            # Document processing
    ├── retrieval/            # Hybrid search (BM25 + Vector)
    ├── generation/           # RAG engine + response cache
    ├── evaluation/           # RAGAS pipeline
    ├── database/             # HR DB client + Query Router
    ├── auth/                 # Google OAuth
    ├── analytics/            # PII-free BigQuery logging
    ├── monitoring/           # Structured JSON logger (Cloud Logging)
    └── ui/                   # Streamlit chat interface
```

---

## GCP Resources Created

| Resource | Details |
|----------|---------|
| Project | hr-rag-dev |
| Region | asia-south1 (Mumbai) |
| VPC | hr-rag-vpc (10.1/10.2 subnets) |
| Cloud Run | hr-rag-engine (auto-scaling) |
| Vector Search | 3072 dims, STREAM_UPDATE mode |
| Cloud SQL | hr-rag-db PostgreSQL (12 employees) |
| Firestore | 10 docs, 44 chunks |
| GCS Buckets | documents, processed, artifacts, audit |
| BigQuery | hr_rag_metrics, hr_rag_analytics |
| Secret Manager | gemini-api-key, hr-db-password |
| KMS | hr-rag-keyring, RSA-4096 signing key |
| Service Accounts | rag-engine-sa, ingestion-sa, evaluation-sa, cicd-sa |
| Cloud Monitoring | Dashboard + 4 alert policies + uptime check |

---

## Roadmap

- Phase 1 — Infrastructure: **COMPLETE**
- Phase 2 — Personal RAG + Auth: **COMPLETE**
- Phase 3 — MLOps:
  - Operational monitoring (dashboards, alerts, structured logging): **COMPLETE**
  - Response caching with BigQuery telemetry: **COMPLETE**
  - Vertex AI Experiments tracking: planned
  - A/B testing framework: planned
  - Automated model retraining: planned
  - Drift monitoring: planned
- Phase 4 — Advanced (planned):
  - Multi-tenancy support
  - Slack/Teams bot integration
  - Mobile app

---

## Author

Chandra Nakkalakunta
Principal Cloud and AI/ML Architect
Hyderabad, India

LinkedIn: https://www.linkedin.com/in/chandra-nakkalakunta
GitHub: https://github.com/chandranakkalakunta
Website: https://chandraailabs.com

---

## Related Projects

- Nova Personal Assistant: https://github.com/chandranakkalakunta/nova-assistant
- Smart Document Q&A Bot: https://github.com/chandranakkalakunta/doc-qa-bot
- AI Resume Analyzer: https://github.com/chandranakkalakunta/resume-analyzer

---

## License

MIT License - feel free to use as reference architecture.
