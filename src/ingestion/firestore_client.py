"""
Firestore Client — Enterprise HR RAG Platform
Handles metadata storage and retrieval
"""
import logging
from datetime import datetime, timezone
from document_processor import DocumentChunk, DocumentMetadata

logger = logging.getLogger(__name__)


class FirestoreClient:
    """Manages document metadata in Firestore."""

    def __init__(self, project_id: str):
        from google.cloud import firestore
        from google.cloud.firestore_v1.base_query import FieldFilter
        self.db = firestore.Client(project=project_id)
        self.FF = FieldFilter
        self.project_id = project_id
        logger.info(f"Firestore client initialized: {project_id}")

    def save_document_metadata(self, metadata) -> str:
        self._supersede_old_versions(metadata.document_id)
        doc_ref = self.db.collection("documents").document()
        doc_ref.set(metadata.to_dict())
        logger.info(f"Metadata saved: {metadata.document_id}")
        return doc_ref.id

    def _supersede_old_versions(self, document_id: str) -> int:
        count = 0
        old_docs = (
            self.db.collection("documents")
            .where(filter=self.FF("document_id", "==", document_id))
            .where(filter=self.FF("status", "==", "active"))
            .stream()
        )
        for doc in old_docs:
            doc.reference.update({
                "status": "superseded",
                "superseded_at": datetime.now(timezone.utc).isoformat()
            })
            count += 1
        return count

    def save_chunks(self, chunks: list, batch_size: int = 500) -> int:
        if not chunks:
            return 0
        self._delete_old_chunks(chunks[0].document_id)
        total_saved = 0
        for i in range(0, len(chunks), batch_size):
            batch = self.db.batch()
            for chunk in chunks[i:i + batch_size]:
                ref = self.db.collection("chunks").document(chunk.chunk_id)
                batch.set(ref, chunk.to_dict())
            batch.commit()
            total_saved += len(chunks[i:i + batch_size])
        logger.info(f"Saved {total_saved} chunks")
        return total_saved

    def _delete_old_chunks(self, document_id: str) -> int:
        count = 0
        old_chunks = (
            self.db.collection("chunks")
            .where(filter=self.FF("document_id", "==", document_id))
            .stream()
        )
        batch = self.db.batch()
        batch_count = 0
        for chunk in old_chunks:
            batch.delete(chunk.reference)
            batch_count += 1
            count += 1
            if batch_count >= 500:
                batch.commit()
                batch = self.db.batch()
                batch_count = 0
        if batch_count > 0:
            batch.commit()
        logger.info(f"Deleted {count} old chunks for {document_id}")
        return count

    def get_active_documents(self) -> list:
        docs = (
            self.db.collection("documents")
            .where(filter=self.FF("status", "==", "active"))
            .stream()
        )
        return [doc.to_dict() for doc in docs]

    def get_document_chunks(self, document_id: str) -> list:
        """Get all chunks for a specific document."""
        chunks = (
            self.db.collection("chunks")
            .where(filter=self.FF("document_id", "==", document_id))
            .stream()
        )
        result = []
        for c in chunks:
            data = c.to_dict()
            text = data.get("text", data.get("chunk_text", ""))
            data["text"] = text
            data["chunk_text"] = text
            result.append(data)
        return result

    def get_all_chunks(self) -> list:
        return [c.to_dict() for c in self.db.collection("chunks").stream()]

    def get_stats(self) -> dict:
        docs = list(
            self.db.collection("documents")
            .where(filter=self.FF("status", "==", "active"))
            .stream()
        )
        chunks = list(self.db.collection("chunks").stream())
        return {
            "active_documents": len(docs),
            "total_chunks": len(chunks),
            "document_ids": [d.to_dict().get("document_id") for d in docs]
        }
