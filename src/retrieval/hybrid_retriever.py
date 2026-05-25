"""
Hybrid Retriever — Enterprise HR RAG Platform
Combines BM25 sparse + Vector Search dense retrieval
with re-ranking for best results
"""
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)) + "/ingestion")

from bm25_indexer import BM25Indexer
from firestore_client import FirestoreClient

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Hybrid retrieval combining:
    1. BM25 sparse retrieval (keyword matching)
    2. Vector Search dense retrieval (semantic)
    3. RRF fusion (Reciprocal Rank Fusion)
    4. Re-ranking (cross-encoder)
    """

    def __init__(
        self,
        project_id: str,
        environment: str = "dev",
        top_k_sparse: int = 10,
        top_k_dense: int = 10,
        top_k_final: int = 5,
        alpha: float = 0.5
    ):
        self.project_id = project_id
        self.environment = environment
        self.top_k_sparse = top_k_sparse
        self.top_k_dense = top_k_dense
        self.top_k_final = top_k_final
        self.alpha = alpha  # 0=sparse only, 1=dense only

        # Firestore for chunk text lookup
        self.firestore = FirestoreClient(project_id=project_id)

        # In-memory chunk cache (avoids Firestore call per query!)
        self._chunk_cache = {}
        self._load_chunk_cache()

        # BM25 retriever - build from Firestore on startup
        self.bm25 = BM25Indexer(
            index_path=f"/tmp/bm25_index_{environment}.pkl"
        )
        self._build_bm25_from_firestore()

        # Vector Search (optional)
        self.vector_search = None
        self.embedder = None

        logger.info("Hybrid retriever initialized!")

    def _build_bm25_from_firestore(self):
        """Build BM25 index from Firestore chunks on startup."""
        import sys, os
        sys.path.insert(0, os.path.dirname(__file__).replace("retrieval", "ingestion"))
        from document_processor import DocumentChunk
        from datetime import datetime, timezone

        try:
            if self.bm25.bm25 is not None:
                logger.info("BM25 index already exists - skipping rebuild")
                return

            logger.info("Building BM25 index from Firestore...")
            chunks_data = self.firestore.get_all_chunks()

            if not chunks_data:
                logger.warning("No chunks in Firestore!")
                return

            chunks = []
            for c in chunks_data:
                chunk = DocumentChunk(
                    chunk_id=c.get("chunk_id", ""),
                    document_id=c.get("document_id", ""),
                    filename=c.get("filename", ""),
                    text=c.get("text", c.get("chunk_text", "")),
                    chunk_index=c.get("chunk_index", 0),
                    word_count=c.get("word_count", 0),
                    char_count=len(c.get("chunk_text", "")),
                    created_at=datetime.now(timezone.utc).isoformat()
                )
                chunks.append(chunk)

            self.bm25.build_index(chunks)
            logger.info(f"BM25 built from Firestore: {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Failed to build BM25 from Firestore: {e}")

    def setup_vector_search(
        self,
        index_endpoint_id: str,
        deployed_index_id: str,
        gemini_api_key: str,
        region: str = "asia-south1"
    ):
        """Setup Vector Search component."""
        try:
            sys.path.insert(0, os.path.dirname(__file__).replace(
                "retrieval", "ingestion"))
            from vector_search_client import VectorSearchClient
            from embedding_generator import EmbeddingGenerator

            self.vector_search = VectorSearchClient(
                project_id=self.project_id,
                region=region,
                index_endpoint_id=index_endpoint_id,
                deployed_index_id=deployed_index_id
            )
            self.embedder = EmbeddingGenerator(api_key=gemini_api_key)
            logger.info("Vector Search enabled!")
        except Exception as e:
            logger.warning(f"Vector Search not available: {e}")

    def retrieve(self, query: str) -> list[dict]:
        """
        Main retrieval method.
        Returns ranked list of relevant chunks.
        """
        logger.info(f"Retrieving for query: {query[:50]}...")

        # Step 1: BM25 sparse retrieval
        sparse_results = self._sparse_retrieve(query)
        logger.info(f"BM25 results: {len(sparse_results)}")

        # Step 2: Dense retrieval (if available)
        dense_results = []
        if self.vector_search and self.embedder:
            dense_results = self._dense_retrieve(query)
            logger.info(f"Dense results: {len(dense_results)}")

        # Step 3: Fuse results
        if dense_results:
            fused = self._reciprocal_rank_fusion(
                sparse_results, dense_results
            )
        else:
            fused = sparse_results

        # Step 4: Get full chunk text from Firestore
        enriched = self._enrich_with_firestore(fused)

        # Step 5: Return top-k
        final = enriched[:self.top_k_final]
        logger.info(f"Final results: {len(final)}")
        return final

    def _sparse_retrieve(self, query: str) -> list[dict]:
        """BM25 sparse retrieval."""
        results = self.bm25.search(query, top_k=self.top_k_sparse)
        return [
            {
                "chunk_id": r["chunk_id"],
                "score": r["score"],
                "text": r["text"],
                "metadata": r["metadata"],
                "source": "bm25"
            }
            for r in results
        ]

    def _dense_retrieve(self, query: str) -> list[dict]:
        """Vector Search dense retrieval."""
        try:
            query_embedding = self.embedder.embed_query(query)
            results = self.vector_search.query(
                query_embedding=query_embedding,
                top_k=self.top_k_dense
            )
            return [
                {
                    "chunk_id": r["id"],
                    "score": r["distance"],
                    "source": "vector_search"
                }
                for r in results
            ]
        except Exception as e:
            logger.warning(f"Dense retrieval failed: {e}")
            return []

    def _reciprocal_rank_fusion(
        self,
        sparse: list[dict],
        dense: list[dict],
        k: int = 60
    ) -> list[dict]:
        """
        Reciprocal Rank Fusion (RRF) algorithm.
        Combines rankings from multiple retrievers.
        RRF score = sum(1 / (k + rank))
        """
        scores = {}

        # Add sparse scores
        for rank, result in enumerate(sparse):
            chunk_id = result["chunk_id"]
            if chunk_id not in scores:
                scores[chunk_id] = {"rrf_score": 0, "data": result, "sources": []}
            scores[chunk_id]["rrf_score"] += (1 - self.alpha) / (k + rank + 1)
            scores[chunk_id]["sources"].append("bm25")

        # Add dense scores
        for rank, result in enumerate(dense):
            chunk_id = result["chunk_id"]
            if chunk_id not in scores:
                scores[chunk_id] = {"rrf_score": 0, "data": result, "sources": []}
            scores[chunk_id]["rrf_score"] += self.alpha / (k + rank + 1)
            scores[chunk_id]["sources"].append("vector_search")

        # Sort by RRF score
        sorted_results = sorted(
            scores.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )

        return [
            {
                **r["data"],
                "rrf_score": r["rrf_score"],
                # Show actual source: hybrid if in both!
                "source": "hybrid" if len(r["sources"]) > 1
                          else r["sources"][0] if r["sources"]
                          else "unknown"
            }
            for r in sorted_results
        ]

    def _load_chunk_cache(self):
        """Load all chunks into memory on startup."""
        try:
            chunks = self.firestore.get_all_chunks()
            self._chunk_cache = {c.get("chunk_id",""): c for c in chunks if c.get("chunk_id")}
            logger.info(f"Chunk cache loaded: {len(self._chunk_cache)} chunks")
        except Exception as e:
            logger.warning(f"Chunk cache load failed: {e}")
            self._chunk_cache = {}

    def _enrich_with_firestore(self, results: list[dict]) -> list[dict]:
        """Enrich results with full chunk data from Firestore."""
        enriched = []
        # Use in-memory cache - saves ~1000ms per query!
        all_chunks = self._chunk_cache if self._chunk_cache else {
            c["chunk_id"]: c for c in self.firestore.get_all_chunks()
        }

        for result in results:
            chunk_id = result.get("chunk_id", "")
            if chunk_id in all_chunks:
                chunk_data = all_chunks[chunk_id]
                enriched.append({
                    "chunk_id": chunk_id,
                    "text": chunk_data.get("text", chunk_data.get("chunk_text", result.get("text", ""))),
                    "document_id": chunk_data.get("document_id", ""),
                    "filename": chunk_data.get("filename", ""),
                    "chunk_index": chunk_data.get("chunk_index", 0),
                    "score": result.get("score", 0),
                    "source": result.get("source", "bm25")
                })
            elif "text" in result:
                enriched.append(result)

        return enriched


if __name__ == "__main__":
    import json

    print("=" * 50)
    print("Hybrid Retriever Test")
    print("=" * 50)

    retriever = HybridRetriever(
        project_id="hr-rag-dev",
        environment="dev",
        top_k_final=3
    )

    queries = [
        "How many annual leave days do employees get?",
        "What is the work from home policy?",
        "How to submit travel expense claims?"
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        results = retriever.retrieve(query)
        print(f"Results: {len(results)}")
        for r in results:
            print(f"  [{r['document_id']}] Score:{r['score']:.3f}")
            print(f"  {r['text'][:80]}...")
