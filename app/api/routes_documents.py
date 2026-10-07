from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.document_service import DocumentService
from app.utils.logging import get_logger

logger = get_logger("routes_documents")
router = APIRouter()

class SummarizeRequest(BaseModel):
    document_id: Optional[str] = None
    text: Optional[str] = None

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Uploads and ingests a document (PDF, DOCX, TXT, CSV, Excel, Image) into the RAG vector store."""
    service = DocumentService(db)
    content = await file.read()
    try:
        result = service.upload_and_process(
            file_bytes=content,
            original_filename=file.filename or "uploaded_file",
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Document ingestion failed: {str(e)}")

@router.get("/documents")
def list_documents(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    """Lists all ingested documents in the platform."""
    service = DocumentService(db)
    return service.list_documents(limit=limit, offset=offset)

@router.get("/documents/{id}")
def get_document(id: str, db: Session = Depends(get_db)):
    """Retrieves document details, metadata, and chunk statistics."""
    service = DocumentService(db)
    doc = service.get_document(id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc

@router.delete("/documents/{id}", status_code=status.HTTP_200_OK)
def delete_document(id: str, db: Session = Depends(get_db)):
    """Deletes a document, its disk file, its database records, and vector store indices."""
    service = DocumentService(db)
    success = service.delete_document(id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return {"message": "Document successfully deleted", "document_id": id}

@router.post("/summarize")
def summarize(payload: SummarizeRequest, db: Session = Depends(get_db)):
    """Summarizes an ingested document or directly provided text."""
    service = DocumentService(db)
    if payload.document_id:
        summary = service.summarize_document(payload.document_id)
        return {"document_id": payload.document_id, "summary": summary}
    elif payload.text:
        summary = service.llm.generate(prompt=f"Summarize the following document text:\n\n{payload.text}")
        return {"summary": summary}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'document_id' or 'text' must be provided.",
        )
