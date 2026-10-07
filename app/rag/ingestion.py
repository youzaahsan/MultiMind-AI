import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.utils.logging import get_logger
from app.utils.file_validation import validate_uploaded_file, sanitize_filename
from app.multimodal.pdf_processor import PDFProcessor
from app.multimodal.docx_processor import DocxProcessor
from app.multimodal.csv_processor import CSVProcessor
from app.multimodal.excel_processor import ExcelProcessor
from app.multimodal.image_processor import ImageProcessor
from app.rag.chunking import IntelligentChunker
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore, get_vector_store
from app.database.repositories import DocumentRepository

logger = get_logger("ingestion_pipeline")

class DocumentIngestionPipeline:
    """
    End-to-end ingestion pipeline:
    Upload -> Validate -> Detect Type -> Extract -> Clean -> Extract Metadata
    -> Intelligent Chunking -> Generate Embeddings -> Vector DB -> Relational DB
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
        chunker: Optional[IntelligentChunker] = None,
    ):
        self.vector_store = vector_store or get_vector_store()
        self.embedding_service = embedding_service or EmbeddingService()
        self.chunker = chunker or IntelligentChunker()

    def process_file(
        self,
        file_bytes: bytes,
        original_filename: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Executes complete ingestion for an uploaded file.
        """
        # 1. Validate
        is_valid, err_msg = validate_uploaded_file(original_filename, file_bytes)
        if not is_valid:
            raise ValueError(f"File validation failed: {err_msg}")

        # 2. Sanitize and store on disk
        clean_name = sanitize_filename(original_filename)
        doc_id = str(uuid.uuid4())
        ext = Path(clean_name).suffix.lower()
        storage_filename = f"{doc_id}_{clean_name}"
        saved_path = settings.UPLOAD_DIR / storage_filename

        with open(saved_path, "wb") as f:
            f.write(file_bytes)

        file_size = len(file_bytes)
        logger.info(f"Saved uploaded file {clean_name} ({file_size} bytes) to {saved_path}")

        # 3. Detect type & Extract
        extracted_data, modality, total_pages = self._extract_content(saved_path, ext)

        # 4. Extract metadata & generate summary
        metadata = extracted_data.get("metadata", {})
        metadata["original_filename"] = original_filename
        metadata["extension"] = ext
        summary = self._generate_brief_summary(extracted_data, clean_name, ext)

        # 5. Intelligent Chunking
        chunks = self.chunker.chunk_document(
            document_id=doc_id,
            filename=clean_name,
            extracted_data=extracted_data,
            modality=modality,
        )

        # 6. Generate Embeddings & Store in Vector DB
        if chunks:
            chunk_texts = [c["content"] for c in chunks]
            embeddings = self.embedding_service.embed_batch(chunk_texts)
            chunk_metas = [c["metadata"] for c in chunks]
            chunk_ids = [c["chunk_id"] for c in chunks]

            self.vector_store.add_texts(
                texts=chunk_texts,
                embeddings=embeddings,
                metadatas=chunk_metas,
                ids=chunk_ids,
            )

        # 7. Store Document & Chunks in Relational Database
        doc_record = DocumentRepository.create(
            db=db,
            filename=clean_name,
            file_path=str(saved_path),
            file_type=ext.replace(".", ""),
            file_size_bytes=file_size,
            total_pages=total_pages,
            metadata_info=metadata,
            summary=summary,
        )
        # Update record ID to match doc_id
        doc_record.id = doc_id
        db.commit()

        if chunks:
            DocumentRepository.add_chunks(db, doc_id, chunks)

        logger.info(f"Successfully ingested '{clean_name}' (ID: {doc_id}) with {len(chunks)} chunks.")

        return {
            "document_id": doc_id,
            "filename": clean_name,
            "file_type": ext,
            "file_size": file_size,
            "total_pages": total_pages,
            "chunks_count": len(chunks),
            "summary": summary,
            "status": "processed",
        }

    def _extract_content(self, file_path: Path, ext: str) -> Tuple[Dict[str, Any], str, int]:
        """Routes file to specific multimodal extractor."""
        if ext == ".pdf":
            processor = PDFProcessor(file_path)
            data = processor.extract()
            return data, "text", data.get("total_pages", 1)

        elif ext == ".docx":
            processor = DocxProcessor(file_path)
            data = processor.extract()
            return data, "text", 1

        elif ext in [".csv"]:
            processor = CSVProcessor(file_path)
            data = processor.extract()
            return data, "table", 1

        elif ext in [".xlsx", ".xls"]:
            processor = ExcelProcessor(file_path)
            data = processor.extract()
            return data, "table", data.get("metadata", {}).get("total_sheets", 1)

        elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
            processor = ImageProcessor(file_path)
            data = processor.extract()
            return data, "image", 1

        elif ext in [".txt"]:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            return {"full_text": text, "metadata": {"filename": file_path.name}}, "text", 1

        else:
            raise ValueError(f"Unsupported file extension: {ext}")

    def _generate_brief_summary(self, data: Dict[str, Any], filename: str, ext: str) -> str:
        """Constructs an initial summary of document properties."""
        if ext == ".pdf":
            pages = data.get("total_pages", 1)
            words = data.get("total_words", 0)
            return f"PDF document '{filename}' with {pages} page(s) and approximately {words} words."
        elif ext == ".docx":
            words = data.get("total_words", 0)
            return f"Word document '{filename}' containing {words} words."
        elif ext == ".csv":
            rows = data.get("metadata", {}).get("rows", 0)
            cols = data.get("metadata", {}).get("columns_count", 0)
            return f"CSV dataset '{filename}' with {rows} rows and {cols} columns."
        elif ext in [".xlsx", ".xls"]:
            sheets = data.get("metadata", {}).get("total_sheets", 1)
            return f"Excel workbook '{filename}' containing {sheets} sheet(s)."
        elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
            meta = data.get("metadata", {})
            return f"Image '{filename}' ({meta.get('width')}x{meta.get('height')}, {meta.get('format')})."
        return f"Text document '{filename}'."
