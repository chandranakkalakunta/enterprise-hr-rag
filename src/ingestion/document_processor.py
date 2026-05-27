"""
Document Processor — Enterprise HR RAG Platform
Handles text extraction, chunking and metadata management
"""
import re
import uuid
import logging
import os
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a single chunk of a document."""
    chunk_id: str
    document_id: str
    filename: str
    text: str
    chunk_index: int
    word_count: int
    char_count: int
    page_number: int = 0
    section: str = ""
    gcs_path: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "filename": self.filename,
            "text": self.text,
            "chunk_index": self.chunk_index,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "page_number": self.page_number,
            "section": self.section,
            "gcs_path": self.gcs_path,
            "created_at": self.created_at
        }


@dataclass
class DocumentMetadata:
    """Represents document metadata stored in Firestore."""
    document_id: str
    filename: str
    gcs_path: str
    version: str
    status: str  # active, superseded, processing, failed
    chunk_count: int
    char_count: int
    effective_date: str
    created_at: str
    last_updated: str
    environment: str
    content_hash: str = ""

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "gcs_path": self.gcs_path,
            "version": self.version,
            "status": self.status,
            "chunk_count": self.chunk_count,
            "char_count": self.char_count,
            "effective_date": self.effective_date,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "environment": self.environment,
            "content_hash": self.content_hash
        }


class DocumentProcessor:
    """
    Handles document processing pipeline:
    1. Text extraction from various formats
    2. Semantic chunking
    3. Metadata generation
    """

    def __init__(
        self,
        chunk_size: int = 1024,
        chunk_overlap: int = 100,
        min_chunk_size: int = 10
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def extract_text(self, content: str, file_type: str = "md") -> str:
        """Extract clean text from document content."""
        if file_type in ["md", "markdown"]:
            return self._extract_from_markdown(content)
        elif file_type == "txt":
            return content.strip()
        else:
            logger.warning(f"Unknown file type: {file_type}, treating as text")
            return content.strip()

    def _extract_from_markdown(self, content: str) -> str:
        """Extract clean text from markdown content."""
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', content)
        text = re.sub(r'`[^`]+`', '', text)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Keep headers as text (remove # symbols)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Remove markdown links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Remove markdown images
        text = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', text)

        # Remove bold/italic markers
        text = re.sub(r'\*{1,3}([^\*]+)\*{1,3}', r'\1', text)
        text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)

        # Remove horizontal rules
        text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)

        # Remove table formatting
        text = re.sub(r'^\|.*\|$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[-|: ]+$', '', text, flags=re.MULTILINE)

        # Remove bullet points
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)

        return text.strip()

    def extract_section(self, text: str, position: int) -> str:
        """Extract section heading for a given text position."""
        lines = text[:position].split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line and len(line) < 100:
                return line[:50]
        return ""

    def chunk_by_words(self, text: str, document_id: str,
                       filename: str, gcs_path: str = "") -> list[DocumentChunk]:
        """
        Chunk text by word count with overlap.
        Respects paragraph boundaries when possible.
        """
        chunks = []
        paragraphs = text.split('\n\n')
        current_words = []
        chunk_index = 0

        for para in paragraphs:
            para_words = para.split()
            if not para_words:
                continue

            # If adding this paragraph exceeds chunk size
            if len(current_words) + len(para_words) > self.chunk_size:
                # Save current chunk if not empty
                if len(current_words) >= self.min_chunk_size:
                    chunk_text = ' '.join(current_words)
                    chunks.append(DocumentChunk(
                        chunk_id=str(uuid.uuid4()),
                        document_id=document_id,
                        filename=filename,
                        text=chunk_text,
                        chunk_index=chunk_index,
                        word_count=len(current_words),
                        char_count=len(chunk_text),
                        gcs_path=gcs_path,
                        created_at=datetime.now(timezone.utc).isoformat()
                    ))
                    chunk_index += 1

                    # Keep overlap words
                    current_words = current_words[-self.chunk_overlap:]

                # If single paragraph is too large, split it
                if len(para_words) > self.chunk_size:
                    for i in range(0, len(para_words), self.chunk_size - self.chunk_overlap):
                        word_slice = para_words[i:i + self.chunk_size]
                        if len(word_slice) >= self.min_chunk_size:
                            chunk_text = ' '.join(word_slice)
                            chunks.append(DocumentChunk(
                                chunk_id=str(uuid.uuid4()),
                                document_id=document_id,
                                filename=filename,
                                text=chunk_text,
                                chunk_index=chunk_index,
                                word_count=len(word_slice),
                                char_count=len(chunk_text),
                                gcs_path=gcs_path,
                                created_at=datetime.now(timezone.utc).isoformat()
                            ))
                            chunk_index += 1
                    current_words = []
                else:
                    current_words = para_words
            else:
                current_words.extend(para_words)

        # Save remaining words
        if len(current_words) >= self.min_chunk_size:
            chunk_text = ' '.join(current_words)
            chunks.append(DocumentChunk(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                filename=filename,
                text=chunk_text,
                chunk_index=chunk_index,
                word_count=len(current_words),
                char_count=len(chunk_text),
                gcs_path=gcs_path,
                created_at=datetime.now(timezone.utc).isoformat()
            ))

        logger.info(f"Created {len(chunks)} chunks from {filename}")
        return chunks

    def create_metadata(
        self,
        document_id: str,
        filename: str,
        gcs_path: str,
        chunk_count: int,
        char_count: int,
        version: str = "1.0",
        environment: str = "dev"
    ) -> DocumentMetadata:
        """Create document metadata object."""
        import hashlib
        content_hash = hashlib.md5(
            f"{document_id}{version}{char_count}".encode(),
            usedforsecurity=False
        ).hexdigest()

        now = datetime.now(timezone.utc).isoformat()
        return DocumentMetadata(
            document_id=document_id,
            filename=filename,
            gcs_path=gcs_path,
            version=version,
            status="active",
            chunk_count=chunk_count,
            char_count=char_count,
            effective_date=now,
            created_at=now,
            last_updated=now,
            environment=environment,
            content_hash=content_hash
        )

    def process_document(
        self,
        content: str,
        filename: str,
        gcs_path: str = "",
        version: str = "1.0",
        environment: str = "dev"
    ) -> tuple[list[DocumentChunk], DocumentMetadata]:
        """
        Full document processing pipeline.
        Returns (chunks, metadata)
        """
        # Generate document ID from filename
        document_id = filename.replace('current/', '')                              .replace('.md', '').replace('.txt', '')                              .replace('.pdf', '').replace('.docx', '')                              .replace('.doc', '').replace('.xlsx', '')                              .replace('.xls', '').replace(' ', '_')                              .lower()

        # Determine file type
        file_type = filename.split('.')[-1].lower()

        # Extract text
        clean_text = self.extract_text(content, file_type)
        logger.info(f"Extracted {len(clean_text)} chars from {filename}")

        # Chunk text
        chunks = self.chunk_by_words(
            text=clean_text,
            document_id=document_id,
            filename=filename,
            gcs_path=gcs_path
        )

        # Create metadata
        metadata = self.create_metadata(
            document_id=document_id,
            filename=filename,
            gcs_path=gcs_path,
            chunk_count=len(chunks),
            char_count=len(clean_text),
            version=version,
            environment=environment
        )

        return chunks, metadata


if __name__ == "__main__":
    # Test the processor
    processor = DocumentProcessor(chunk_size=512, chunk_overlap=50)

    # Test with sample content
    sample = """
# TechCorp India - Employee Leave Policy

## Annual Leave
Employees are entitled to 21 days of annual leave per year.
Leave must be applied 2 weeks in advance.

## Sick Leave
10 days of sick leave are provided annually.
Medical certificate required for more than 3 consecutive days.
"""
    chunks, metadata = processor.process_document(
        content=sample,
        filename="test_policy.md",
        gcs_path="gs://hr-rag-dev-documents/current/test_policy.md"
    )

    print(f"✅ Chunks: {len(chunks)}")
    print(f"✅ Metadata: {metadata.document_id}")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i}: {chunk.word_count} words")
