import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.config.settings import settings
from app.utils.logging import get_logger

logger = get_logger("chunking")

class IntelligentChunker:
    """
    Splits document text into semantic chunks based on headings, paragraphs,
    page boundaries, and tables while maintaining metadata and configurable overlap.
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def chunk_document(
        self,
        document_id: str,
        filename: str,
        extracted_data: Dict[str, Any],
        modality: str = "text",
    ) -> List[Dict[str, Any]]:
        """
        Chunks extracted document content respecting structure and boundaries.
        """
        chunks: List[Dict[str, Any]] = []

        # If data has structured pages (like PDF)
        if "pages" in extracted_data and extracted_data["pages"]:
            for page_info in extracted_data["pages"]:
                page_num = page_info.get("page_number", 1)
                page_text = page_info.get("text", "")
                headings = page_info.get("headings", [])
                current_heading = headings[0] if headings else None

                page_chunks = self._split_text_by_paragraphs(
                    text=page_text,
                    document_id=document_id,
                    filename=filename,
                    page=page_num,
                    section=current_heading,
                    modality="text",
                    base_index=len(chunks),
                )
                chunks.extend(page_chunks)

        # If data is DOCX with structured paragraphs and tables
        elif "paragraphs" in extracted_data or "tables" in extracted_data:
            section_title = None
            text_blocks: List[str] = []

            for p in extracted_data.get("paragraphs", []):
                if p.get("is_heading"):
                    # Process accumulated blocks
                    if text_blocks:
                        combined = "\n\n".join(text_blocks)
                        p_chunks = self._split_text_by_paragraphs(
                            text=combined,
                            document_id=document_id,
                            filename=filename,
                            page=1,
                            section=section_title,
                            modality="text",
                            base_index=len(chunks),
                        )
                        chunks.extend(p_chunks)
                        text_blocks = []
                    section_title = p.get("text")
                else:
                    text_blocks.append(p.get("text", ""))

            if text_blocks:
                combined = "\n\n".join(text_blocks)
                p_chunks = self._split_text_by_paragraphs(
                    text=combined,
                    document_id=document_id,
                    filename=filename,
                    page=1,
                    section=section_title,
                    modality="text",
                    base_index=len(chunks),
                )
                chunks.extend(p_chunks)

            # Add table chunks separately
            for tbl in extracted_data.get("tables", []):
                table_md = tbl.get("markdown", "")
                if table_md:
                    chunks.append(self._create_chunk(
                        document_id=document_id,
                        filename=filename,
                        chunk_index=len(chunks),
                        content=f"Table Data:\n{table_md}",
                        page=1,
                        section="Tables",
                        modality="table",
                    ))

        # If data is structured sheets (Excel)
        elif "sheets" in extracted_data and extracted_data["sheets"]:
            for sheet_name, sheet_info in extracted_data["sheets"].items():
                content = f"Sheet: {sheet_name}\nRows: {sheet_info.get('rows')}, Columns: {', '.join(sheet_info.get('columns', []))}\n"
                for col, stat in sheet_info.get("statistics", {}).items():
                    content += f"Column '{col}' statistics: {stat}\n"
                chunks.append(self._create_chunk(
                    document_id=document_id,
                    filename=filename,
                    chunk_index=len(chunks),
                    content=content,
                    page=1,
                    section=f"Sheet: {sheet_name}",
                    modality="table",
                ))

        # Fallback or generic text (CSV, TXT, Image text summary)
        else:
            full_text = extracted_data.get("full_text", "")
            if full_text:
                chunks = self._split_text_by_paragraphs(
                    text=full_text,
                    document_id=document_id,
                    filename=filename,
                    page=1,
                    section=None,
                    modality=modality,
                    base_index=0,
                )

        logger.info(f"Chunked document '{filename}' into {len(chunks)} intelligent chunks.")
        return chunks

    def _split_text_by_paragraphs(
        self,
        text: str,
        document_id: str,
        filename: str,
        page: int,
        section: Optional[str],
        modality: str,
        base_index: int,
    ) -> List[Dict[str, Any]]:
        """Splits text by natural paragraph boundaries into chunk_size windows with overlap."""
        if not text.strip():
            return []

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [text.strip()]

        chunks: List[Dict[str, Any]] = []
        current_chunk_words: List[str] = []
        current_section = section

        for para in paragraphs:
            # Check if this paragraph itself looks like a heading
            if len(para) < 80 and not para.endswith((".", ",", ":", ";")) and len(para.split()) < 10:
                current_section = para

            words = para.split()
            if not words:
                continue

            # If paragraph fits in chunk_size, create chunk directly
            if len(words) <= self.chunk_size:
                chunks.append(self._create_chunk(
                    document_id=document_id,
                    filename=filename,
                    chunk_index=base_index + len(chunks),
                    content=para,
                    page=page,
                    section=current_section,
                    modality=modality,
                ))
            else:
                # Split large paragraph into chunk_size windows with overlap
                curr_idx = 0
                while curr_idx < len(words):
                    sub_words = words[curr_idx : curr_idx + self.chunk_size]
                    chunks.append(self._create_chunk(
                        document_id=document_id,
                        filename=filename,
                        chunk_index=base_index + len(chunks),
                        content=" ".join(sub_words),
                        page=page,
                        section=current_section,
                        modality=modality,
                    ))
                    curr_idx += (self.chunk_size - self.chunk_overlap)
                    if curr_idx >= len(words):
                        break

        return chunks

    def _create_chunk(
        self,
        document_id: str,
        filename: str,
        chunk_index: int,
        content: str,
        page: int,
        section: Optional[str],
        modality: str,
    ) -> Dict[str, Any]:
        return {
            "chunk_id": str(uuid.uuid4()),
            "document_id": document_id,
            "filename": filename,
            "chunk_index": chunk_index,
            "content": content,
            "page_number": page,
            "section": section or "General",
            "modality": modality,
            "token_count": len(content.split()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "document_id": document_id,
                "filename": filename,
                "page": page,
                "section": section or "General",
                "chunk_index": chunk_index,
                "modality": modality,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        }
