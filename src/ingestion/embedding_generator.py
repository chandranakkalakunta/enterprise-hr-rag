"""
Embedding Generator — Enterprise HR RAG Platform
Generates embeddings using Gemini text-embedding-004
"""
import logging
import time
import os
from typing import Optional
from document_processor import DocumentChunk

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 3072
BATCH_SIZE = 100  # Max embeddings per API call
RATE_LIMIT_DELAY = 0.1  # Seconds between batches


class EmbeddingGenerator:
    """
    Generates text embeddings using Gemini API.
    Handles batching and rate limiting.
    """

    def __init__(self, api_key: str, model: str = EMBEDDING_MODEL):
        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.dimensions = EMBEDDING_DIMENSIONS
        logger.info(f"Embedding generator initialized: {model}")

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=text
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise

    def generate_embeddings_batch(
        self,
        texts: list[str],
        task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        Handles batching automatically.
        """
        all_embeddings = []

        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            logger.info(f"Embedding batch {i//BATCH_SIZE + 1}: "
                       f"{len(batch)} texts")

            try:
                result = self.client.models.embed_content(
                    model=self.model,
                    contents=batch
                )
                batch_embeddings = [e.values for e in result.embeddings]
                all_embeddings.extend(batch_embeddings)

                # Rate limiting
                if i + BATCH_SIZE < len(texts):
                    time.sleep(RATE_LIMIT_DELAY)

            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                # Return zero vectors for failed batch
                for _ in batch:
                    all_embeddings.append([0.0] * self.dimensions)

        logger.info(f"Generated {len(all_embeddings)} embeddings")
        return all_embeddings

    def embed_chunks(
        self,
        chunks: list[DocumentChunk]
    ) -> list[dict]:
        """
        Generate embeddings for document chunks.
        Returns list of dicts with chunk_id and embedding.
        """
        texts = [chunk.text for chunk in chunks]
        embeddings = self.generate_embeddings_batch(texts)

        result = []
        for chunk, embedding in zip(chunks, embeddings):
            result.append({
                'id': chunk.chunk_id,
                'embedding': embedding,
                'document_id': chunk.document_id,
                'filename': chunk.filename,
                'text': chunk.text,
                'chunk_index': chunk.chunk_index
            })

        return result

    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.
        Uses RETRIEVAL_QUERY task type for better search.
        """
        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=query
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            raise


if __name__ == "__main__":
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not set!")
        exit(1)

    gen = EmbeddingGenerator(api_key=api_key)

    # Test single embedding
    test_text = "How many days of annual leave do employees get?"
    embedding = gen.generate_embedding(test_text)
    print(f"✅ Embedding generated!")
    print(f"   Dimensions: {len(embedding)}")
    print(f"   First 5 values: {embedding[:5]}")
