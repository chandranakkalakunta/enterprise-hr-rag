"""
Startup Warmup Script
Runs when Cloud Run instance starts
Pre-builds BM25 index so first query is fast!
"""
import sys, os, logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def warmup():
    """Pre-initialize all heavy components."""
    try:
        logger.info("Warming up RAG engine...")

        sys.path.insert(0, "src/generation")
        sys.path.insert(0, "src/retrieval")
        sys.path.insert(0, "src/ingestion")

        project_id = os.environ.get("PROJECT_ID", "hr-rag-dev")
        api_key = os.environ.get("GEMINI_API_KEY", "")
        environment = os.environ.get("ENVIRONMENT", "dev")

        if not api_key:
            logger.warning("No API key - skipping warmup")
            return

        from rag_engine import RAGEngine
        engine = RAGEngine(
            project_id=project_id,
            gemini_api_key=api_key,
            environment=environment
        )

        # Trigger a simple query to warm everything up
        result = engine.query("What is the leave policy?")
        logger.info(f"Warmup complete! Answer length: {len(result.get('answer',''))}")

    except Exception as e:
        logger.error(f"Warmup failed: {e}")

if __name__ == "__main__":
    warmup()
