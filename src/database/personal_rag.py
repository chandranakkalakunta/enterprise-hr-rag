"""
Personal RAG - ChandraAILabs HR RAG Platform
Handles personalized HR queries using employee data
"""
import logging
import os
import sys

logger = logging.getLogger(__name__)


class PersonalRAG:
    """
    Handles personal HR queries by combining:
    1. Employee data from Cloud SQL
    2. Policy context from RAG
    3. Gemini for natural language response
    """

    def __init__(
        self,
        project_id: str,
        gemini_api_key: str,
        model: str = "gemini-2.5-flash"
    ):
        self.project_id = project_id
        self.model = model

        from google import genai
        self.client = genai.Client(api_key=gemini_api_key)

        # Initialize DB client
        from hr_db_client import HRDBClient
        self.db = HRDBClient(
            project_id=project_id,
            instance_name=os.environ.get("DB_INSTANCE_NAME", "hr-rag-db"),
            db_name=os.environ.get("DB_NAME", "hr_db"),
            db_user=os.environ.get("DB_USER", "hr_admin"),
            db_password=os.environ.get("DB_PASSWORD", "ChandraAILabs2024!"),
            region=os.environ.get("REGION", "asia-south1")
        )

        # Initialize query router
        from query_router import QueryRouter
        self.router = QueryRouter()

        logger.info("Personal RAG initialized!")

    def query(
        self,
        question: str,
        employee_email: str,
        policy_rag_engine=None
    ) -> dict:
        """
        Process a personal query.
        Returns personalized answer with context.
        """
        import time
        start_time = time.time()

        # Get employee profile
        employee = self.db.get_employee_by_email(employee_email)
        if not employee:
            return {
                "answer": "I could not find your employee profile. Please contact HR.",
                "sources": [],
                "intent": "error",
                "employee": {}
            }

        # Detect intent
        intent = self.router.detect_intent(question)

        # Get personal context
        personal_context = self.router.get_personal_context(
            question, employee, self.db
        )

        # Get policy context if needed
        policy_context = ""
        if intent in ["hybrid", "policy"] and policy_rag_engine:
            try:
                policy_result = policy_rag_engine.retriever.retrieve(question)
                policy_chunks = [
                    f"[{c.get('document_id', '')}] {c.get('text', '')}"
                    for c in policy_result[:3]
                ]
                policy_context = "\n\n".join(policy_chunks)
            except Exception as e:
                logger.warning(f"Policy context failed: {e}")

        # Build prompt
        prompt = self._build_prompt(
            question=question,
            employee=employee,
            personal_context=personal_context,
            policy_context=policy_context,
            intent=intent
        )

        # Generate answer
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            answer = response.text
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            answer = f"Sorry, I could not generate an answer. Error: {e}"

        # Log analytics (anonymized - no PII!)
        try:
            import sys
            analytics_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../analytics")
            sys.path.insert(0, analytics_path)
            from analytics_logger import AnalyticsLogger, hash_user_id
            al = AnalyticsLogger(project_id=self.project_id)
            latency_ms = int((time.time() - start_time) * 1000)
            al.log_query_async(
                question=question,
                intent=intent,
                employee_email=employee_email,
                department=employee.get("department"),
                chunks_retrieved=0,
                latency_ms=latency_ms,
                model_used=self.model,
                success=True
            )
        except Exception as e:
            logger.warning(f"Analytics logging failed: {e}")

        return {
            "answer": answer,
            "sources": ["HR Database", "HR Policies"] if policy_context else ["HR Database"],
            "intent": intent,
            "employee": {
                "name": employee.get("name"),
                "employee_id": employee.get("employee_id"),
                "designation": employee.get("designation")
            }
        }

    def _build_prompt(
        self,
        question: str,
        employee: dict,
        personal_context: str,
        policy_context: str,
        intent: str
    ) -> str:
        """Build personalized prompt."""

        name = employee.get("name", "Employee")

        prompt = f"""You are a personal HR assistant for ChandraAILabs.
You are speaking directly with {name}.
Always address them by their first name and be warm and helpful.

EMPLOYEE PERSONAL DATA:
{personal_context}
"""
        if policy_context:
            prompt += f"""
RELEVANT HR POLICIES:
{policy_context}
"""

        prompt += f"""
EMPLOYEE QUESTION: {question}

INSTRUCTIONS:
- Address {name.split()[0]} directly by first name
- Give a specific, personalized answer using their actual data
- For personal data (leave/CTC/rating): use the exact numbers above
- For policy questions: reference the policy documents
- For hybrid: combine personal data with policy context
- Be conversational, warm and helpful
- Keep response concise and clear

PERSONALIZED ANSWER:"""

        return prompt
