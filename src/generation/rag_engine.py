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
            top_k_final=5
        )

        logger.info(f"RAG Engine initialized: {model}")

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
- Answer clearly and concisely
- Always cite which policy document your answer comes from
- Use format: "According to [Policy Name]..."
- If multiple policies apply, reference all of them
- Be helpful and professional

ANSWER:"""
        return prompt

    def query(self, question: str) -> dict:
        """
        Process a query through the RAG pipeline.
        Returns answer with citations and metadata.
        """
        logger.info(f"Processing query: {question[:50]}...")

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
        return result

    def query_stream(self, question: str):
        """
        Stream response for better UX.
        Yields text chunks as they are generated.
        """
        chunks = self.retriever.retrieve(question)

        if not chunks:
            yield "I could not find relevant information in our HR policies."
            return

        prompt = self.build_prompt(question, chunks)

        try:
            response = self.client.models.generate_content_stream(
                model=self.model,
                contents=prompt
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Error: {e}"


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
