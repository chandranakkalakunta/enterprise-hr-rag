"""
Ingestion Pipeline — Enterprise HR RAG Platform
Orchestrates full document ingestion:
1. Read from GCS
2. Process (extract + chunk)
3. Generate embeddings
4. Update Vector Search
5. Update BM25 index
6. Save metadata to Firestore
"""
import logging
import os
import sys
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Add parent to path
sys.path.insert(0, os.path.dirname(__file__))

from document_processor import DocumentProcessor
from enhanced_document_processor import EnhancedDocumentProcessor
from embedding_generator import EmbeddingGenerator
from bm25_indexer import BM25Indexer
from firestore_client import FirestoreClient


class IngestionPipeline:
    """
    Full document ingestion pipeline.
    Handles all steps from GCS to Vector Search.
    """

    def __init__(
        self,
        project_id: str,
        region: str,
        index_endpoint_id: str,
        deployed_index_id: str,
        gemini_api_key: str,
        environment: str = "dev"
    ):
        self.project_id = project_id
        self.region = region
        self.environment = environment

        # Initialize components
        self.processor = DocumentProcessor(
            chunk_size=int(os.environ.get("CHUNK_SIZE", "1024")),
            chunk_overlap=int(os.environ.get("CHUNK_OVERLAP", "100")),
            min_chunk_size=int(os.environ.get("MIN_CHUNK_SIZE", "10"))
        )
        # Enhanced processor for PDF/Word/Excel/Images
        self.enhanced_processor = EnhancedDocumentProcessor(
            gemini_api_key=os.environ.get("GEMINI_API_KEY", "")
        )
        self.embedder = EmbeddingGenerator(api_key=gemini_api_key)
        self.bm25 = BM25Indexer(
            index_path=f"/tmp/bm25_index_{environment}.pkl"
        )
        self.firestore = FirestoreClient(project_id=project_id)

        # Vector Search (optional - may not be deployed yet)
        self.vector_search = None
        try:
            from vector_search_client import VectorSearchClient
            self.vector_search = VectorSearchClient(
                project_id=project_id,
                region=region,
                index_endpoint_id=index_endpoint_id,
                deployed_index_id=deployed_index_id
            )
            logger.info("Vector Search client initialized")
        except Exception as e:
            logger.warning(f"Vector Search not available: {e}")
            logger.warning("Continuing without Vector Search...")

        logger.info("Ingestion pipeline initialized!")

    def ingest_from_gcs(
        self,
        bucket_name: str,
        blob_name: str,
        version: str = "1.0"
    ) -> dict:
        """
        Ingest a document from GCS.
        Returns ingestion result summary.
        """
        from google.cloud import storage

        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting ingestion: gs://{bucket_name}/{blob_name}")

        try:
            # Step 0: Cleanup old data
            logger.info("Step 0: Cleaning up old data...")
            document_id = blob_name.replace('current/', '').replace('.md', '').replace('.txt', '').replace('.pdf', '').replace('.docx', '').replace('.doc', '').replace('.xlsx', '').replace('.xls', '')

            # Delete old chunks from Firestore and get their IDs
            old_chunks = self.firestore.get_document_chunks(document_id)
            old_chunk_ids = [c.get('chunk_id', '') for c in old_chunks if c.get('chunk_id')]

            # Delete old embeddings from Vector Search
            if old_chunk_ids and self.vector_search:
                self.vector_search.delete_embeddings(old_chunk_ids)
                logger.info(f"Deleted {len(old_chunk_ids)} old embeddings")

            # Step 1: Read from GCS
            logger.info("Step 1: Reading from GCS...")
            storage_client = storage.Client(project=self.project_id)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            gcs_path = f"gs://{bucket_name}/{blob_name}"

            # Detect file format
            file_ext = blob_name.lower().split(".")[-1] if "." in blob_name else "md"
            logger.info(f"File format: {file_ext}")

            # Step 2: Extract text based on format
            logger.info("Step 2: Processing document...")

            if file_ext in ["pdf", "docx", "doc", "xlsx", "xls"]:
                # Download to temp file for binary formats
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as tmp:
                    blob.download_to_filename(tmp.name)
                    tmp_path = tmp.name

                logger.info(f"Extracting text from {file_ext.upper()} file...")
                extracted_text = self.enhanced_processor.process_file(tmp_path)

                import os as _os
                _os.unlink(tmp_path)

                if not extracted_text:
                    logger.warning(f"No text extracted from {blob_name}")
                    return None, None

                logger.info(f"Extracted {len(extracted_text)} chars from {file_ext.upper()}")
                doc_content = extracted_text
            else:
                # Markdown/text: download as text directly
                doc_content = blob.download_as_text()
                logger.info(f"Read {len(doc_content)} chars")

            # For non-markdown files use extracted text as markdown
            process_filename = blob_name
            if file_ext in ["pdf", "docx", "doc", "xlsx", "xls"]:
                process_filename = blob_name.rsplit(".", 1)[0] + ".md"

            chunks, metadata = self.processor.process_document(
                content=doc_content,
                filename=process_filename,
                gcs_path=gcs_path,
                version=version,
                environment=self.environment
            )
            logger.info(f"Created {len(chunks)} chunks")

            # Step 3: Generate embeddings
            logger.info("Step 3: Generating embeddings...")
            embedded_chunks = self.embedder.embed_chunks(chunks)
            logger.info(f"Generated {len(embedded_chunks)} embeddings")

            # Step 4: Update Vector Search
            if self.vector_search:
                logger.info("Step 4: Updating Vector Search...")
                success = self.vector_search.upsert_embeddings(embedded_chunks)
                if success:
                    logger.info("Vector Search updated!")
                else:
                    logger.warning("Vector Search update failed - continuing")
            else:
                logger.warning("Step 4: Vector Search not available")

            # Step 5: Update BM25 index
            logger.info("Step 5: Updating BM25 index...")
            self.bm25.build_index(chunks)
            logger.info("BM25 index updated!")

            # Step 6: Save metadata to Firestore
            logger.info("Step 6: Saving metadata to Firestore...")
            doc_ref_id = self.firestore.save_document_metadata(metadata)
            chunk_count = self.firestore.save_chunks(chunks)
            logger.info(f"Metadata saved: {doc_ref_id}")

            # Calculate duration
            duration = (datetime.now(timezone.utc) - start_time).seconds

            result = {
                "status": "success",
                "filename": blob_name,
                "document_id": metadata.document_id,
                "chunks": len(chunks),
                "embeddings": len(embedded_chunks),
                "duration_seconds": duration,
                "gcs_path": gcs_path
            }

            logger.info(f"✅ Ingestion complete: {result}")
            return result

        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            return {
                "status": "failed",
                "filename": blob_name,
                "error": str(e)
            }

    def ingest_all_documents(
        self,
        bucket_name: str,
        prefix: str = "current/"
    ) -> list[dict]:
        """
        Ingest all documents from a GCS bucket prefix.
        Returns list of ingestion results.
        """
        from google.cloud import storage

        logger.info(f"Ingesting all documents from gs://{bucket_name}/{prefix}")

        storage_client = storage.Client(project=self.project_id)
        bucket = storage_client.bucket(bucket_name)
        blobs = list(bucket.list_blobs(prefix=prefix))

        results = []
        for blob in blobs:
            if blob.name.endswith(('.md', '.txt', '.pdf', '.docx', '.doc', '.xlsx', '.xls')):
                result = self.ingest_from_gcs(
                    bucket_name=bucket_name,
                    blob_name=blob.name
                )
                results.append(result)
                logger.info(f"Ingested: {blob.name} → {result['status']}")

        logger.info(f"Ingestion complete: {len(results)} documents")
        return results


if __name__ == "__main__":
    import json

    # Configuration from environment
    project_id = os.environ.get('PROJECT_ID', 'hr-rag-dev')
    region = os.environ.get('REGION', 'asia-south1')
    api_key = os.environ.get('GEMINI_API_KEY', '')
    bucket = os.environ.get('DOCS_BUCKET', 'hr-rag-dev-documents')

    # Vector Search endpoint
    endpoint_id = os.environ.get(
        'VECTOR_ENDPOINT_ID',
        'projects/946703664996/locations/asia-south1/indexEndpoints/2379105667995664384'
    )
    deployed_index_id = os.environ.get(
        'DEPLOYED_INDEX_ID',
        'hr_rag_deployed_index'
    )

    print("=" * 50)
    print("HR RAG Platform - Ingestion Pipeline Test")
    print("=" * 50)

    # Initialize pipeline
    pipeline = IngestionPipeline(
        project_id=project_id,
        region=region,
        index_endpoint_id=endpoint_id,
        deployed_index_id=deployed_index_id,
        gemini_api_key=api_key,
        environment="dev"
    )

    # Test with single document
    print("\nTesting single document ingestion...")
    result = pipeline.ingest_from_gcs(
        bucket_name=bucket,
        blob_name="current/01_leave_policy.md"
    )
    print(f"\nResult: {json.dumps(result, indent=2)}")
