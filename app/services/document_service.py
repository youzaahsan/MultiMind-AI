from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.database.models import Document
from app.database.repositories import DocumentRepository
from app.rag.ingestion import DocumentIngestionPipeline
from app.rag.vector_store import get_vector_store
from app.services.llm_service import get_llm_service
from app.utils.logging import get_logger

logger = get_logger("document_service")

class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.pipeline = DocumentIngestionPipeline()
        self.vector_store = get_vector_store()
        self.llm = get_llm_service()

    def upload_and_process(
        self,
        file_bytes: bytes,
        original_filename: str,
    ) -> Dict[str, Any]:
        """Ingests, chunks, embeds, and stores uploaded file."""
        return self.pipeline.process_file(
            file_bytes=file_bytes,
            original_filename=original_filename,
            db=self.db,
        )

    def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        docs = DocumentRepository.get_all(self.db, limit=limit, offset=offset)
        return [
            {
                "id": d.id,
                "filename": d.filename,
                "file_type": d.file_type,
                "file_size": d.file_size_bytes,
                "total_pages": d.total_pages,
                "chunk_count": d.chunk_count,
                "status": d.status,
                "summary": d.summary,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ]

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        doc = DocumentRepository.get_by_id(self.db, doc_id)
        if not doc:
            return None
        return {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size_bytes,
            "total_pages": doc.total_pages,
            "chunk_count": doc.chunk_count,
            "status": doc.status,
            "metadata": doc.metadata_info,
            "summary": doc.summary,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        }

    def delete_document(self, doc_id: str) -> bool:
        doc = DocumentRepository.get_by_id(self.db, doc_id)
        if not doc:
            return False

        # 1. Delete physical file if exists
        try:
            if doc.file_path and Path(doc.file_path).exists():
                Path(doc.file_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Could not remove file on disk: {e}")

        # 2. Remove from vector store
        self.vector_store.delete_by_document_id(doc_id)

        # 3. Delete from DB (cascades to chunks)
        return DocumentRepository.delete(self.db, doc_id)

    def summarize_document(self, doc_id: str) -> str:
        doc = DocumentRepository.get_by_id(self.db, doc_id)
        if not doc:
            return "Document not found."

        chunks = doc.chunks
        if not chunks:
            return "No content available in document to summarize."

        combined_text = "\n\n".join([c.content for c in chunks[:5]])
        prompt = f"Summarize the following document content comprehensively:\n\n{combined_text}"
        return self.llm.generate(prompt=prompt)
