"""
BM25 Indexer — Enterprise HR RAG Platform
Handles sparse retrieval using BM25 algorithm
"""
import logging
import json
import os
import pickle
from typing import Optional
from document_processor import DocumentChunk

logger = logging.getLogger(__name__)


class BM25Indexer:
    """
    BM25 sparse retrieval index.
    Complements dense Vector Search for hybrid retrieval.
    """

    def __init__(self, index_path: str = "/tmp/bm25_index.pkl"):
        self.index_path = index_path
        self.bm25 = None
        self.chunk_ids = []
        self.chunk_texts = []
        self.chunk_metadata = []
        self._load_index()

    def _load_index(self):
        """Load existing index from disk if available."""
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'rb') as f:
                    data = pickle.load(f)
                    self.bm25 = data['bm25']
                    self.chunk_ids = data['chunk_ids']
                    self.chunk_texts = data['chunk_texts']
                    self.chunk_metadata = data['chunk_metadata']
                logger.info(f"BM25 index loaded: {len(self.chunk_ids)} chunks")
            except Exception as e:
                logger.warning(f"Could not load index: {e}")

    def _save_index(self):
        """Save index to disk."""
        try:
            with open(self.index_path, 'wb') as f:
                pickle.dump({
                    'bm25': self.bm25,
                    'chunk_ids': self.chunk_ids,
                    'chunk_texts': self.chunk_texts,
                    'chunk_metadata': self.chunk_metadata
                }, f)
            logger.info(f"BM25 index saved: {len(self.chunk_ids)} chunks")
        except Exception as e:
            logger.error(f"Could not save index: {e}")

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization."""
        import re
        # Lowercase and split on non-alphanumeric
        tokens = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
        # Remove very short tokens
        return [t for t in tokens if len(t) > 2]

    def build_index(self, chunks: list[DocumentChunk]) -> bool:
        """Build BM25 index from chunks."""
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            logger.warning("rank_bm25 not installed! pip install rank-bm25")
            return False

        try:
            # Remove existing chunks for same documents
            doc_ids = set(c.document_id for c in chunks)
            self._remove_document_chunks(doc_ids)

            # Add new chunks
            for chunk in chunks:
                self.chunk_ids.append(chunk.chunk_id)
                self.chunk_texts.append(chunk.text)
                self.chunk_metadata.append({
                    'document_id': chunk.document_id,
                    'filename': chunk.filename,
                    'chunk_index': chunk.chunk_index
                })

            # Rebuild BM25 index
            tokenized = [self._tokenize(text) for text in self.chunk_texts]
            self.bm25 = BM25Okapi(tokenized)

            # Save to disk
            self._save_index()

            logger.info(f"BM25 index built: {len(self.chunk_ids)} total chunks")
            return True

        except Exception as e:
            logger.error(f"Index build failed: {e}")
            return False

    def _remove_document_chunks(self, document_ids: set):
        """Remove chunks for specified documents."""
        indices_to_keep = [
            i for i, meta in enumerate(self.chunk_metadata)
            if meta.get('document_id') not in document_ids
        ]

        self.chunk_ids = [self.chunk_ids[i] for i in indices_to_keep]
        self.chunk_texts = [self.chunk_texts[i] for i in indices_to_keep]
        self.chunk_metadata = [self.chunk_metadata[i] for i in indices_to_keep]

    def search(
        self,
        query: str,
        top_k: int = 10
    ) -> list[dict]:
        """
        Search using BM25.
        Returns list of {chunk_id, score, metadata} dicts.
        """
        if not self.bm25 or not self.chunk_ids:
            logger.warning("BM25 index is empty!")
            return []

        try:
            # Tokenize query
            query_tokens = self._tokenize(query)
            if not query_tokens:
                return []

            # Get BM25 scores
            scores = self.bm25.get_scores(query_tokens)

            # Get top-k results
            top_indices = sorted(
                range(len(scores)),
                key=lambda i: scores[i],
                reverse=True
            )[:top_k]

            results = []
            for idx in top_indices:
                if scores[idx] > 0:
                    results.append({
                        'chunk_id': self.chunk_ids[idx],
                        'score': float(scores[idx]),
                        'text': self.chunk_texts[idx],
                        'metadata': self.chunk_metadata[idx]
                    })

            logger.info(f"BM25 search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []

    def get_stats(self) -> dict:
        """Get index statistics."""
        return {
            'total_chunks': len(self.chunk_ids),
            'index_built': self.bm25 is not None,
            'index_path': self.index_path
        }


if __name__ == "__main__":
    # Install rank-bm25 if needed
    import subprocess
    subprocess.run(['pip', 'install', 'rank-bm25', '--quiet'])

    from document_processor import DocumentProcessor

    # Test with sample
    processor = DocumentProcessor(min_chunk_size=5)
    chunks, _ = processor.process_document(
        content="""
# Leave Policy
Employees get 21 days annual leave per year.
Sick leave is 10 days annually.
Maternity leave is 26 weeks for female employees.
""",
        filename="test_leave.md"
    )

    indexer = BM25Indexer(index_path="/tmp/test_bm25.pkl")
    indexer.build_index(chunks)

    results = indexer.search("annual leave days", top_k=3)
    print(f"✅ BM25 search results: {len(results)}")
    for r in results:
        print(f"  Score: {r['score']:.3f} | {r['text'][:60]}...")
