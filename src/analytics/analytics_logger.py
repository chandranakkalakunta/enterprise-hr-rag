"""
Analytics Logger - ChandraAILabs HR RAG Platform
Logs query analytics to BigQuery - fully anonymized, no PII!
"""
import hashlib
import logging
import os
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

QUESTION_CATEGORIES = {
    "leave":        ["leave", "vacation", "time off", "casual", "sick", "annual", "maternity", "paternity"],
    "compensation": ["ctc", "salary", "pay", "compensation", "bonus", "increment", "hike"],
    "performance":  ["rating", "performance", "review", "appraisal", "pip", "promotion"],
    "wfh":          ["wfh", "work from home", "remote", "hybrid"],
    "benefits":     ["insurance", "health", "pf", "provident", "gratuity", "esop"],
    "policy":       ["policy", "rule", "guideline", "process", "procedure"],
    "onboarding":   ["onboarding", "joining", "probation", "induction"],
    "grievance":    ["grievance", "complaint", "posh", "harassment"],
    "training":     ["training", "certification", "course", "learning"],
    "travel":       ["travel", "expense", "reimbursement", "trip"],
    "security":     ["password", "security", "data", "device", "it"],
}


def categorize_question(question: str) -> str:
    """Categorize question without storing actual text."""
    q_lower = question.lower()
    for category, keywords in QUESTION_CATEGORIES.items():
        if any(kw in q_lower for kw in keywords):
            return category
    return "general"


def hash_user_id(user_identifier: str, salt: str = "chandraailabs_2026") -> str:
    """One-way hash - cannot be reversed to original."""
    combined = f"{user_identifier}:{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


class AnalyticsLogger:
    """Logs query analytics to BigQuery - NO PII stored!"""

    def __init__(self, project_id: str, environment: str = "dev"):
        self.project_id = project_id
        self.environment = environment
        self._bq_client = None

    def _get_bq_client(self):
        if not self._bq_client:
            from google.cloud import bigquery
            self._bq_client = bigquery.Client(project=self.project_id)
        return self._bq_client

    def log_query(
        self,
        question: str,
        intent: str = "policy",
        employee_email: str = None,
        department: str = None,
        chunks_retrieved: int = 0,
        latency_ms: int = 0,
        model_used: str = "gemini-2.5-flash",
        success: bool = True,
        session_id: str = None
    ):
        """Log query analytics - anonymized, no PII!"""
        try:
            client = self._get_bq_client()
            table_id = f"{self.project_id}.hr_rag_metrics.query_logs"

            hashed_user = hash_user_id(employee_email) if employee_email else None
            question_category = categorize_question(question)

            row = {
                "query_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hashed_user_id": hashed_user,
                "department": department,
                "intent": intent,
                "question_category": question_category,
                "chunks_retrieved": chunks_retrieved,
                "latency_ms": latency_ms,
                "model_used": model_used,
                "success": success,
                "environment": self.environment,
                "session_id": session_id or str(uuid.uuid4())
            }

            errors = client.insert_rows_json(table_id, [row])
            if errors:
                logger.warning(f"BigQuery insert errors: {errors}")
            else:
                logger.info(f"Analytics logged: {question_category}/{intent}")

        except Exception as e:
            logger.warning(f"Analytics logging failed: {e}")
