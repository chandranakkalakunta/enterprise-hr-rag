# ============================================================
# Makefile — Enterprise HR RAG Platform
# Simple commands for common operations
# Usage: make <command>
# ============================================================

.PHONY: help setup-dev setup-prod deploy-dev deploy-prod \
        evaluate test ingest check-index push clean \
        teardown-dev logs costs

# Default target
help:
	@echo ""
	@echo "Enterprise HR RAG Platform — Available Commands"
	@echo "================================================="
	@echo ""
	@echo "Setup:"
	@echo "  make setup-dev       Full dev environment setup"
	@echo "  make setup-prod      Full prod environment setup"
	@echo ""
	@echo "Deploy:"
	@echo "  make deploy-dev      Deploy RAG app to dev"
	@echo "  make deploy-prod     Deploy RAG app to prod"
	@echo ""
	@echo "Data:"
	@echo "  make ingest          Upload HR documents"
	@echo "  make check-index     Check Vector Search status"
	@echo "  make deploy-index    Deploy index to endpoint"
	@echo ""
	@echo "Quality:"
	@echo "  make evaluate        Run RAGAS evaluation"
	@echo "  make test            Run unit tests"
	@echo ""
	@echo "Operations:"
	@echo "  make logs            Tail Cloud Run logs"
	@echo "  make costs           Show current GCP costs"
	@echo "  make push            Git add, commit, push"
	@echo ""
	@echo "Cleanup:"
	@echo "  make teardown-dev    Delete dev resources"
	@echo ""

# ── Setup ──────────────────────────────────────────────────
setup-env:
	@./scripts/setup_environment.sh

setup-dev:
	@echo "Setting up dev environment..."
	@./setup_all.sh --env=dev --skip-org

setup-prod:
	@echo "Setting up prod environment..."
	@./setup_all.sh --env=prod

# ── Deploy ─────────────────────────────────────────────────
deploy-dev:
	@./scripts/08_rag_deployment.sh --env=dev

deploy-prod:
	@./scripts/08_rag_deployment.sh --env=prod

# ── Data ───────────────────────────────────────────────────
ingest:
	@./scripts/upload_documents.sh --env=dev --dir=./data/documents

upload:
	@./scripts/upload_documents.sh --env=dev --dir=./data/documents

ingest-pipeline:
	@./scripts/ingest_documents.sh --env=dev
	@echo "Restarting Cloud Run to clear response cache..."
	@gcloud run services update hr-rag-engine --region=asia-south1 --project=hr-rag-dev --set-env-vars="CACHE_BUST=$$(date +%s)" --quiet 2>/dev/null || true

check-index:
	@gcloud ai indexes list \
		--region=asia-south1 \
		--project=hr-rag-dev \
		--format="table(displayName,state,createTime)"

deploy-index:
	@./scripts/06b_deploy_index.sh --env=dev

# ── Quality ────────────────────────────────────────────────
evaluate:
	@echo "Running RAGAS evaluation..."
	@./venv/bin/python3 src/evaluation/ragas_evaluator.py

test:
	@echo "Running tests..."
	@python3 -m pytest tests/ -v

# ── Operations ─────────────────────────────────────────────
logs:
	@gcloud run services logs read hr-rag-engine \
		--project=hr-rag-dev \
		--region=asia-south1 \
		--limit=50

costs:
	@echo "Current GCP costs:"
	@gcloud billing projects describe hr-rag-dev \
		--format="table(billingAccountName,billingEnabled)"

push:
	@git add .
	@git commit -m "Update: $(shell date '+%Y-%m-%d %H:%M')"
	@git push origin main
	@echo "✅ Pushed to GitHub!"

# ── Cleanup ────────────────────────────────────────────────
teardown-dev:
	@echo "⚠️  WARNING: This will delete ALL dev resources!"
	@read -p "Type 'yes' to confirm: " confirm && \
		[ "$$confirm" = "yes" ] && \
		./teardown/destroy_all.sh --env=dev || \
		echo "Teardown cancelled!"
