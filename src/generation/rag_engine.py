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


class RAGEngine:
    """
    RAG Engine for HR Policy Q&A.
    Retrieves relevant chunks and generates answers with citations.
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

        # Initialize Gemini client
        from google import genai
        self.client = genai.Client(api_key=gemini_api_key)

        # Initialize retriever
        self.retriever = HybridRetriever(
            project_id=project_id,
            environment=environment,
            top_k_final=3
        )

        # Enable Vector Search
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

        # Simple response cache (TTL: 30 mins)
        # Shorter TTL ensures stale data cleared faster
        self._cache = {}
        self._cache_ttl = 1800

    def invalidate_cache(self):
        """Clear response cache - call after re-ingestion!"""
        self._cache = {}
        logger.info("Response cache invalidated!")


    def build_prompt(self, query: str, chunks: list[dict]) -> str:
        """Build prompt with retrieved context."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            doc_id = chunk.get("document_id", "unknown")
            text = chunk.get("text", "")
            context_parts.append(
                f"[Source {i}: {doc_id}]\n{text}"
            )

        context = "\n\n".join(context_parts)

        prompt = f"""You are an HR assistant for TechCorp India.
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
        return prompt

    def query(self, question: str) -> dict:
        """
        Process a query through the RAG pipeline.
        Returns answer with citations and metadata.
        """
        logger.info(f"Processing query: {question[:50]}...")
        import time, hashlib
        start_time = time.time()

        # Check cache first!
        cache_key = hashlib.md5(question.lower().strip().encode()).hexdigest()
        if cache_key in self._cache:
            cached_time, cached_result = self._cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                logger.info("Cache hit!")
                # Still log cache hits to BigQuery!
                try:
                    import sys as _sys
                    import os as _os
                    _analytics_path = _os.path.join(
                        _os.path.dirname(_os.path.abspath(__file__)), "../analytics"
                    )
                    _sys.path.insert(0, _analytics_path)
                    from analytics_logger import AnalyticsLogger
                    al = AnalyticsLogger(
                        project_id=self.project_id,
                        environment=self.environment
                    )
                    al.log_query_async(
                        question=question,
                        intent="policy",
                        chunks_retrieved=0,
                        latency_ms=0,
                        model_used="cache",
                        success=True
                    )
                except Exception as e:
                    logger.warning(f"Cache hit logging failed: {e}")
                return cached_result

        # Step 1: Retrieve relevant chunks
        chunks = self.retriever.retrieve(question)

        if not chunks:
            return {
                "answer": "I could not find relevant information in our HR policies.",
                "sources": [],
                "chunks_used": 0,
                "question": question
            }

        # Step 2: Build prompt
        prompt = self.build_prompt(question, chunks)

        # Step 3: Generate answer
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            answer = response.text

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            answer = f"Error generating answer: {e}"

        # Step 4: Extract sources
        sources = list(set([
            c.get("document_id", "unknown")
            for c in chunks
        ]))

        result = {
            "question": question,
            "answer": answer,
            "sources": sources,
            "chunks_used": len(chunks),
            "chunks": [
                {
                    "document_id": c.get("document_id"),
                    "text": c.get("text", "")[:200],
                    "score": c.get("score", 0)
                }
                for c in chunks
            ]
        }

        logger.info(f"Answer generated using {len(chunks)} chunks")

        # Log to BigQuery (anonymized - no PII!)
        try:
            import sys
            analytics_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../analytics")
            sys.path.insert(0, analytics_path)
            from analytics_logger import AnalyticsLogger
            al = AnalyticsLogger(project_id=self.project_id, environment=self.environment)
            latency_ms = int((time.time() - start_time) * 1000)
            al.log_query_async(
                question=question,
                intent=result.get("intent", "policy"),
                chunks_retrieved=len(chunks),
                latency_ms=latency_ms,
                model_used=self.model,
                success=True
            )
        except Exception as e:
            logger.warning(f"Analytics logging failed: {e}")

        # Cache the result
        self._cache[cache_key] = (time.time(), result)
        # Keep cache size manageable
        if len(self._cache) > 100:
            oldest = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest]

        return result

    def query_stream(self, question: str):
        """
        Stream response for better UX.
        Yields text chunks as they are generated.
        """
        import time as _time
        _start = _time.time()

        chunks = self.retriever.retrieve(question)

        if not chunks:
            yield "I could not find relevant information in our HR policies."
            return

        prompt = self.build_prompt(question, chunks)
        full_answer = ""

        try:
            response = self.client.models.generate_content_stream(
                model=self.model,
                contents=prompt
            )
            for chunk in response:
                if chunk.text:
                    full_answer += chunk.text
                    yield chunk.text
        except Exception as e:
            yield f"Error: {e}"

        # Log analytics after streaming completes
        try:
            import sys as _sys, os as _os
            _analytics_path = _os.path.join(
                _os.path.dirname(_os.path.abspath(__file__)), "../analytics"
            )
            _sys.path.insert(0, _analytics_path)
            from analytics_logger import AnalyticsLogger
            al = AnalyticsLogger(project_id=self.project_id, environment=self.environment)
            al.log_query_async(
                question=question,
                intent="policy",
                chunks_retrieved=len(chunks),
                latency_ms=int((_time.time() - _start) * 1000),
                model_used=self.model,
                success=True
            )
        except Exception as e:
            logger.warning(f"Stream analytics failed: {e}")


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
