import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pypdf import PdfReader
from app.utils.logging import get_logger

logger = get_logger("pdf_processor")

class PDFProcessor:
    """Extracts text, headings, structure, and metadata from PDF files."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

    def extract(self) -> Dict[str, Any]:
        """
        Parses the PDF and returns structured data preserving pages and metadata.
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.file_path}")

        reader = PdfReader(str(self.file_path))
        num_pages = len(reader.pages)
        raw_meta = reader.metadata or {}
        
        pdf_metadata = {
            "title": str(raw_meta.get("/Title", "") or ""),
            "author": str(raw_meta.get("/Author", "") or ""),
            "creator": str(raw_meta.get("/Creator", "") or ""),
            "total_pages": num_pages,
            "filename": self.file_path.name,
            "file_size": self.file_path.stat().st_size,
        }

        pages_data: List[Dict[str, Any]] = []
        full_text_list: List[str] = []

        for idx, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            clean_page_text = self._clean_text(page_text)
            headings = self._detect_headings(clean_page_text)
            tables = self._detect_tables(clean_page_text)

            pages_data.append({
                "page_number": idx,
                "text": clean_page_text,
                "headings": headings,
                "tables": tables,
                "char_count": len(clean_page_text),
                "word_count": len(clean_page_text.split()),
            })
            if clean_page_text:
                full_text_list.append(clean_page_text)

        combined_text = "\n\n".join(full_text_list)

        return {
            "metadata": pdf_metadata,
            "total_pages": num_pages,
            "pages": pages_data,
            "full_text": combined_text,
            "total_words": sum(p["word_count"] for p in pages_data),
        }

    def _clean_text(self, text: str) -> str:
        """Cleans irregular whitespace, non-printable characters, and page artifacts."""
        if not text:
            return ""
        # Normalize newlines
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Replace multiple spaces with single space
        text = re.sub(r"[ \t]+", " ", text)
        # Strip trailing whitespaces per line
        lines = [line.strip() for line in text.split("\n")]
        # Remove consecutive blank lines
        clean_lines = []
        for line in lines:
            if line or (clean_lines and clean_lines[-1]):
                clean_lines.append(line)
        return "\n".join(clean_lines).strip()

    def _detect_headings(self, text: str) -> List[str]:
        """Detects section titles, headings, and chapter markers."""
        headings = []
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Pattern 1: Chapter / Section / numbered headers e.g. "1. Introduction" or "Chapter 2"
            if re.match(r"^(chapter\s+\d+|section\s+\d+|\d+(\.\d+)*\s+[A-Z])", line, re.I):
                headings.append(line)
            # Pattern 2: Short uppercase lines
            elif len(line) < 60 and line.isupper() and len(line.split()) <= 7:
                headings.append(line)
            # Pattern 3: Capitalized short headings without ending punctuation
            elif len(line) < 50 and line.istitle() and not line.endswith((".", ",", ";", ":")):
                if len(line.split()) <= 6:
                    headings.append(line)
        return headings

    def _detect_tables(self, text: str) -> List[str]:
        """Heuristic table detector for tab/pipe separated lines."""
        tables = []
        current_table = []
        for line in text.split("\n"):
            # Table-like indicators: pipes or multiple aligned tabs/numbers
            if "|" in line or re.search(r"\S+\s{3,}\S+\s{3,}\S+", line):
                current_table.append(line)
            else:
                if len(current_table) >= 2:
                    tables.append("\n".join(current_table))
                current_table = []
        if len(current_table) >= 2:
            tables.append("\n".join(current_table))
        return tables
