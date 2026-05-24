# Enterprise HR RAG Platform

> Reference-grade Enterprise RAG on Google Cloud Platform

A production-ready HR Policy Q&A system built with hybrid RAG architecture,
enterprise security, personal data integration, and privacy-compliant analytics.

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
```
|
v
Query Router
(Intent Detection)
/      |      Personal  Policy  Hybrid
|        |       |
Cloud SQL  BM25 +  Both
HR DB    Vector   Combined
\       |      /
\      v     /
Gemini 2.5 Flash
|
v
Personalized Answer

Citations + Sources
|
v
BigQuery Analytics
(Anonymized - No PII!)


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
| Audit | Cloud Logging + BigQuery (PII-free) |

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
- latency_ms, success, timestamp

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
| Personal Data | Cloud SQL PostgreSQL |
| Metadata Store | Google Firestore |
| Analytics | BigQuery (anonymized) |
| Document Store | Google Cloud Storage |
| UI | Streamlit |
| Auth | Google OAuth |
| Deployment | Google Cloud Run |
| Security | Binary Authorization + KMS |
| IaC | 14 Shell Scripts + Makefile |

---

## Evaluation Results

| Metric | BM25 Only | Hybrid RAG | Improvement |
|--------|-----------|------------|-------------|
| Avg Relevancy | 0.635 | 0.674 | +6.1% |
| Source Accuracy | 1.000 | 1.000 | Maintained |
| Easy Questions | 0.706 | 0.740 | +4.8% |
| Medium Questions | 0.611 | 0.630 | +3.1% |
| Hard Questions | 0.377 | 0.522 | +38.5% |

---

## Analytics Insights (Live Data)

| Intent | Category | Avg Latency | Count |
|--------|----------|-------------|-------|
| policy | leave | 7,426ms | 3 |
| policy | wfh | 6,790ms | 2 |
| policy | training | 4,518ms | 2 |
| personal | compensation | 2,248ms | 1 |
| personal | general | 2,121ms | 1 |
| hybrid | performance | 5,998ms | 1 |

Personal queries 3x faster than policy queries!

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
```

---

## Project Structure
enterprise-hr-rag/
setup_all.sh              - ONE command setup
Makefile                  - Developer commands
requirements.txt          - Python dependencies
Dockerfile                - Container definition
config/                   - Environment configs
scripts/                  - IaC scripts 00-14
00_prerequisites.sh
01_org_setup.sh
02_project_setup.sh     - 19 APIs enabled
03_networking.sh        - VPC + subnets + NAT
04_security.sh          - IAM + KMS + Binary Auth
05_storage.sh           - GCS + BigQuery + Firestore
06_vector_search.sh     - Vertex AI Vector Search
07_data_pipeline.sh     - Cloud Functions
08_rag_deployment.sh    - Cloud Run deployment
09_monitoring.sh        - Dashboards + Alerts
10_evaluation.sh        - RAGAS pipeline
11_cicd.sh              - Cloud Build CI/CD
12_hr_database.sh       - Cloud SQL PostgreSQL
13_hr_data_load.sh      - Sample employee data
ingest_documents.sh     - Document ingestion
verify_ingestion.sh     - Verification
upload_documents.sh     - Full upload pipeline
src/
ingestion/              - Document processing
retrieval/              - Hybrid search (BM25 + Vector)
generation/             - RAG engine (Gemini)
evaluation/             - RAGAS pipeline
database/               - HR DB client + Query Router
auth/                   - Google OAuth
analytics/              - PII-free BigQuery logging
ui/                     - Streamlit chat interface
data/
documents/              - 10 ChandraAILabs HR policies
ground_truth/           - 20 Q&A evaluation dataset
teardown/                 - Cleanup scripts

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

---

## Roadmap

Phase 1 - Infrastructure: COMPLETE
Phase 2 - Personal RAG + Auth: COMPLETE
Phase 3 - MLOps (planned):
  - Vertex AI Experiments tracking
  - A/B testing framework
  - Automated model retraining
  - Drift monitoring

Phase 4 - Advanced (planned):
  - Multi-tenancy support
  - Slack/Teams bot integration
  - Analytics dashboard
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
