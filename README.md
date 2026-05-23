# Enterprise HR RAG Platform

> Reference-grade Enterprise RAG on Google Cloud Platform

A production-ready HR Policy Q&A system built with hybrid RAG architecture,
enterprise security, and automated evaluation pipeline.

Live Demo: https://hr-rag-engine-946703664996.asia-south1.run.app

---

## What It Does

Employees ask natural language questions about HR policies and get
accurate, cited answers instantly.

| Question | Source |
|----------|--------|
| How many leave days do I get? | Leave Policy |
| What is the WFH policy? | Remote Work Policy |
| How do I claim travel expenses? | Travel and Expense Policy |
| What is the PIP process? | Performance Management |

---

## Architecture
Employee Query
|
v
Streamlit Chat UI (Cloud Run)
|
v
RAG Engine
|           |
BM25        Vector Search
(Sparse)    (Dense 3072 dims)
|           |
+-----+-----+
|
RRF Fusion
|
Gemini 2.5 Flash
|
Answer + Citations

---

## Security Architecture

| Layer | Implementation |
|-------|---------------|
| Secret Management | Google Cloud Secret Manager |
| Identity | Dedicated Service Accounts (least privilege) |
| Supply Chain | Binary Authorization + KMS RSA-4096 |
| Encryption | CMEK with Cloud KMS |
| Audit | Cloud Logging (7-year retention) |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Gemini 2.5 Flash |
| Embeddings | gemini-embedding-001 (3072 dims) |
| Dense Retrieval | Vertex AI Vector Search |
| Sparse Retrieval | BM25 (rank-bm25) |
| Metadata Store | Google Firestore |
| Analytics | BigQuery |
| Document Store | Google Cloud Storage |
| UI | Streamlit |
| Deployment | Google Cloud Run |
| Security | Binary Authorization + KMS |
| IaC | Shell scripts + Makefile |

---

## Evaluation Results

| Metric | Score |
|--------|-------|
| Avg Relevancy | 0.635 |
| Source Accuracy | 1.000 |
| Easy Questions | 0.706 |
| Medium Questions | 0.611 |
| Hard Questions | 0.377 |

---

## Quick Start

Clone repository:
  git clone https://github.com/chandranakkalakunta/enterprise-hr-rag
  cd enterprise-hr-rag

Setup environment:
  make setup-env

Setup GCP infrastructure:
  make setup-dev

Ingest documents:
  make ingest-pipeline

Run evaluation:
  make evaluate

Deploy to Cloud Run:
  make deploy-dev

---

## Project Structure

enterprise-hr-rag/
  setup_all.sh              - ONE command setup
  Makefile                  - Simple developer commands
  config/                   - Environment configs (dev/prod)
  scripts/                  - IaC scripts 00-11
    00_prerequisites.sh     - Check tools
    01_org_setup.sh         - GCP Organization
    02_project_setup.sh     - Projects and APIs
    03_networking.sh        - VPC and subnets
    04_security.sh          - IAM, KMS, Binary Auth
    05_storage.sh           - GCS, BigQuery, Firestore
    06_vector_search.sh     - Vertex AI Vector Search
    07_data_pipeline.sh     - Cloud Functions
    08_rag_deployment.sh    - Cloud Run deployment
    09_monitoring.sh        - Dashboards and alerts
    10_evaluation.sh        - RAGAS pipeline
    11_cicd.sh              - Cloud Build CI/CD
  src/
    ingestion/              - Document processing pipeline
    retrieval/              - Hybrid search (BM25 + Vector)
    generation/             - RAG engine with Gemini
    evaluation/             - RAGAS evaluation pipeline
    ui/                     - Streamlit chat interface
  data/
    documents/              - 10 HR policy documents
    ground_truth/           - 20 Q&A evaluation dataset
  teardown/                 - Cleanup scripts

---

## Roadmap

Phase 1 - Infrastructure (COMPLETE):
  - GCP Organization structure
  - VPC and Networking
  - Security (SA, KMS, Binary Auth)
  - Storage (GCS, BigQuery, Firestore)
  - Vector Search (3072 dims, streaming)
  - IaC scripts (one command setup)

Phase 2 - Data Pipeline (COMPLETE):
  - 10 HR policy documents
  - Auto-ingestion via Cloud Function
  - Text extraction and chunking
  - Embedding generation (3072 dims)
  - Firestore metadata management

Phase 3 - RAG Application (COMPLETE):
  - BM25 sparse retrieval
  - Vector Search dense retrieval
  - RRF hybrid fusion
  - Gemini 2.5 Flash generation
  - Citation tracking
  - Streamlit UI deployed on Cloud Run

Phase 4 - Evaluation (COMPLETE):
  - 20 Q&A ground truth dataset
  - Automated evaluation pipeline
  - BigQuery results storage

Phase 5 - Coming Soon:
  - MLOps pipeline (Vertex AI Experiments)
  - A/B testing for RAG configurations
  - Personal data (leave balance queries)
  - Multi-tenancy support
  - CI/CD pipeline (Cloud Build)

---

## GCP Resources Created

| Resource | Details |
|----------|---------|
| Project | hr-rag-dev |
| Region | asia-south1 (Mumbai) |
| VPC | hr-rag-vpc |
| Cloud Run | hr-rag-engine |
| Vector Search | 3072 dims, STREAM_UPDATE |
| Firestore | 10 docs, 41 chunks |
| GCS Buckets | documents, processed, artifacts, audit |
| BigQuery | hr_rag_metrics, hr_rag_analytics |
| Secret Manager | gemini-api-key, rag-config |
| KMS | hr-rag-keyring, RSA-4096 signing key |

---

## Author

Chandra Nakkalakunta
Principal Cloud and AI/ML Architect

LinkedIn: https://www.linkedin.com/in/chandra-nakkalakunta
GitHub: https://github.com/chandranakkalakunta

---

## Related Projects

- Nova Personal Assistant: https://github.com/chandranakkalakunta/nova-assistant
- Smart Document Q&A Bot: https://github.com/chandranakkalakunta/doc-qa-bot
- AI Resume Analyzer: https://github.com/chandranakkalakunta/resume-analyzer
- AI Job Search Agent: https://github.com/chandranakkalakunta/job-search-agent

---

## License

MIT License - feel free to use as reference architecture.
