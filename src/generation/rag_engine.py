"""
RAG Engine — Enterprise HR RAG Platform
Combines retrieval + generation for HR Q&A
"""
import logging
import os
import sys
sys.path.insert(0, os.path.dirname(__file__).replace("generation", "retrieval"))
sys.path.insert(0, os.path.dirname(__file__).replace("generation", "ingestion"))

from hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)

_ANALYTICS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../analytics")


def _log(project_id, environment, **kwargs):
    """Fire-and-forget analytics log."""
    try:
        sys.path.insert(0, _ANALYTICS_PATH)
        from analytics_logger import AnalyticsLogger
        AnalyticsLogger(project_id=project_id, environment=environment).log_query_async(**kwargs)
    except Exception as e:
        logger.warning(f"Analytics logging failed: {e}")


class RAGEngine:
    """
    RAG Engine for HR Policy Q&A.
    Retrieves relevant chunks and generates answers with citations.

    Cache hierarchy:
      L1 — in-memory dict (per instance, TTL 30 min)
      L2 — Firestore collection 'rag_cache' (shared across instances, TTL 24 h)
    """

    def __init__(
        self,
        project_id: str,
        gemini_api_key: str,
        environment: str = "dev",
        model: str = "gemini-2.5-flash"
    ):
        self.project_id = project_id
        self.environment = environment
        self.model = model

        from google import genai
        self.client = genai.Client(api_key=gemini_api_key)

        self.retriever = HybridRetriever(
            project_id=project_id,
            environment=environment,
            top_k_final=3
        )

        endpoint_id = os.environ.get(
            'VECTOR_ENDPOINT_ID',
            'projects/946703664996/locations/asia-south1/indexEndpoints/2379105667995664384'
        )
        deployed_index_id = os.environ.get('DEPLOYED_INDEX_ID', 'hr_rag_deployed_index')
        region = os.environ.get('REGION', 'asia-south1')

        try:
            self.retriever.setup_vector_search(
                index_endpoint_id=endpoint_id,
                deployed_index_id=deployed_index_id,
                gemini_api_key=gemini_api_key,
                region=region
            )
            logger.info("Vector Search enabled in RAG engine!")
        except Exception as e:
            logger.warning(f"Vector Search not available: {e}")

        logger.info(f"RAG Engine initialized: {model}")

        # L1 cache — in-memory, per instance
        self._cache = {}
        self._cache_ttl = 1800  # 30 min

        # L2 cache — Firestore, shared and persistent (lazy init)
        self._fs_client = None
        self._fs_ttl_hours = 24

    # ── Firestore L2 cache helpers ─────────────────────────

    def _get_fs_client(self):
        if not self._fs_client:
            from google.cloud import firestore
            self._fs_client = firestore.Client(project=self.project_id)
        return self._fs_client

    def _fs_doc_id(self, cache_key: str) -> str:
        return f"{self.environment}_{cache_key}"

    def _fs_cache_get(self, cache_key: str) -> dict | None:
        try:
            from datetime import datetime, timezone
            doc = self._get_fs_client().collection("rag_cache").document(
                self._fs_doc_id(cache_key)
            ).get()
            if not doc.exists:
                return None
            data = doc.to_dict()
            expires_at = datetime.fromisoformat(data["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                return None
            return data["result"]
        except Exception as e:
            logger.warning(f"Firestore cache read failed: {e}")
            return None

    def _fs_cache_set(self, cache_key: str, result: dict):
        """Write to Firestore in a background thread — never blocks the response."""
        import threading
        threading.Thread(target=self._fs_cache_write, args=(cache_key, result), daemon=True).start()

    def _fs_cache_write(self, cache_key: str, result: dict):
        try:
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            self._get_fs_client().collection("rag_cache").document(
                self._fs_doc_id(cache_key)
            ).set({
                "result": result,
                "created_at": now.isoformat(),
                "expires_at": (now + timedelta(hours=self._fs_ttl_hours)).isoformat(),
                "environment": self.environment,
            })
            logger.info("L2 cache written to Firestore")
        except Exception as e:
            logger.warning(f"Firestore cache write failed: {e}")

    # ── Cache invalidation ─────────────────────────────────

    def invalidate_cache(self):
        """Clear L1 + L2 cache — call after re-ingestion."""
        self._cache = {}
        try:
            from google.cloud.firestore_v1.base_query import FieldFilter
            docs = self._get_fs_client().collection("rag_cache").where(
                filter=FieldFilter("environment", "==", self.environment)
            ).stream()
            batch = self._get_fs_client().batch()
            count = 0
            for doc in docs:
                batch.delete(doc.reference)
                count += 1
                if count % 500 == 0:
                    batch.commit()
                    batch = self._get_fs_client().batch()
            if count % 500 != 0:
                batch.commit()
            logger.info(f"Cache invalidated: L1 + {count} Firestore entries")
        except Exception as e:
            logger.warning(f"Firestore cache invalidation failed: {e}")
            logger.info("Cache invalidated: L1 only")

    # ── Prompt builder ─────────────────────────────────────

    def build_prompt(self, query: str, chunks: list[dict]) -> str:
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            doc_id = chunk.get("document_id", "unknown")
            text = chunk.get("text", "")
            context_parts.append(f"[Source {i}: {doc_id}]\n{text}")

        context = "\n\n".join(context_parts)

        return f"""You are an HR assistant for ChandraAILabs.
Answer the employee question based ONLY on the HR policy documents provided.
If the answer is not in the documents, say "I don't have information about this in our HR policies."

HR POLICY DOCUMENTS:
{context}

EMPLOYEE QUESTION: {query}

INSTRUCTIONS:
- Answer concisely in 3-5 sentences maximum
- Always cite the source policy document
- Use format: "According to [Policy Name]..."
- Give the key facts only, not exhaustive details
- Be helpful and professional
- If employee wants more details, they can ask follow-up

ANSWER:"""

    # ── query() ───────────────────────────────────────────

    def query(self, question: str) -> dict:
        import time, hashlib
        start_time = time.time()
        cache_key = hashlib.md5(question.lower().strip().encode(), usedforsecurity=False).hexdigest()

        # L1 check
        if cache_key in self._cache:
            cached_time, cached_result = self._cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                logger.info("Cache hit (L1)")
                _log(self.project_id, self.environment, question=question, intent="policy",
                     chunks_retrieved=0, latency_ms=0, model_used="cache_l1", success=True)
                return cached_result

        # L2 check
        fs_result = self._fs_cache_get(cache_key)
        if fs_result:
            logger.info("Cache hit (L2 Firestore)")
            self._cache[cache_key] = (time.time(), fs_result)  # warm L1
            _log(self.project_id, self.environment, question=question, intent="policy",
                 chunks_retrieved=0, latency_ms=0, model_used="cache_l2", success=True)
            return fs_result

        # Full pipeline
        chunks = self.retriever.retrieve(question)
        if not chunks:
            return {"answer": "I could not find relevant information in our HR policies.",
                    "sources": [], "chunks_used": 0, "question": question}

        prompt = self.build_prompt(question, chunks)
        try:
            response = self.client.models.generate_content(model=self.model, contents=prompt)
            answer = response.text
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            answer = f"Error generating answer: {e}"

        sources = list(set(c.get("document_id", "unknown") for c in chunks))
        result = {
            "question": question,
            "answer": answer,
            "sources": sources,
            "chunks_used": len(chunks),
            "chunks": [{"document_id": c.get("document_id",""), "text": c.get("text",""),
                        "score": c.get("score", 0), "gcs_path": c.get("gcs_path","")} for c in chunks[:3]],
        }

        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Answer generated using {len(chunks)} chunks in {latency_ms}ms")
        _log(self.project_id, self.environment, question=question, intent="policy",
             chunks_retrieved=len(chunks), latency_ms=latency_ms, model_used=self.model, success=True)

        # Store in L1 + L2
        self._cache[cache_key] = (time.time(), result)
        if len(self._cache) > 100:
            oldest = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest]
        self._fs_cache_set(cache_key, result)

        return result

    # ── query_stream() ────────────────────────────────────

    def query_stream(self, question: str):
        import time as _time, hashlib
        _start = _time.time()
        cache_key = hashlib.md5(question.lower().strip().encode(), usedforsecurity=False).hexdigest()

        # L1 check
        if cache_key in self._cache:
            cached_time, cached_result = self._cache[cache_key]
            if _time.time() - cached_time < self._cache_ttl:
                logger.info("Cache hit (L1 stream)")
                _log(self.project_id, self.environment, question=question, intent="policy",
                     chunks_retrieved=0, latency_ms=0, model_used="cache_l1", success=True)
                yield cached_result.get("answer", "")
                return

        # L2 check
        fs_result = self._fs_cache_get(cache_key)
        if fs_result:
            logger.info("Cache hit (L2 Firestore stream)")
            self._cache[cache_key] = (_time.time(), fs_result)  # warm L1
            _log(self.project_id, self.environment, question=question, intent="policy",
                 chunks_retrieved=0, latency_ms=0, model_used="cache_l2", success=True)
            yield fs_result.get("answer", "")
            return

        # Full pipeline
        chunks = self.retriever.retrieve(question)
        if not chunks:
            yield "I could not find relevant information in our HR policies."
            return

        prompt = self.build_prompt(question, chunks)
        full_answer = ""

        try:
            response = self.client.models.generate_content_stream(model=self.model, contents=prompt)
            for chunk in response:
                if chunk.text:
                    full_answer += chunk.text
                    yield chunk.text
        except Exception as e:
            yield f"Error: {e}"

        if full_answer:
            result = {
                "question": question,
                "answer": full_answer,
                "sources": list(set(c.get("document_id", "unknown") for c in chunks)),
                "chunks_used": len(chunks),
                "chunks": [{"document_id": c.get("document_id",""), "text": c.get("text",""),
                            "score": c.get("score", 0), "gcs_path": c.get("gcs_path","")} for c in chunks[:3]],
            }
            # Store in L1 + L2
            self._cache[cache_key] = (_time.time(), result)
            if len(self._cache) > 100:
                oldest = min(self._cache, key=lambda k: self._cache[k][0])
                del self._cache[oldest]
            self._fs_cache_set(cache_key, result)

        latency_ms = int((_time.time() - _start) * 1000)
        _log(self.project_id, self.environment, question=question, intent="policy",
             chunks_retrieved=len(chunks), latency_ms=latency_ms, model_used=self.model, success=True)


if __name__ == "__main__":
    print("=" * 50)
    print("RAG Engine Test")
    print("=" * 50)

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Set GEMINI_API_KEY!")
        exit(1)

    engine = RAGEngine(
        project_id="hr-rag-dev",
        gemini_api_key=api_key,
        environment="dev"
    )

    questions = [
        "How many annual leave days do I get?",
        "What is the work from home policy?",
        "How do I submit travel expense claims?"
    ]

    for question in questions:
        print(f"\nQ: {question}")
        result = engine.query(question)
        print(f"A: {result['answer'][:300]}...")
        print(f"Sources: {result['sources']}")
        print(f"Chunks used: {result['chunks_used']}")
        print("-" * 40)
