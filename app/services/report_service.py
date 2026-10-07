import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.database.repositories import AnalyticsRepository
from app.services.llm_service import get_llm_service
from app.utils.logging import get_logger

logger = get_logger("report_service")

class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.llm = get_llm_service()

    def generate_report(
        self,
        topic: str,
        context: Optional[str] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generates a structured comprehensive intelligence report."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        prompt = (
            f"Generate a professional, structured intelligence report on the topic: '{topic}'.\n"
            f"Context:\n{context or 'Analyze core principles, methodologies, findings, and strategic takeaways.'}\n\n"
            "Format the report with sections:\n"
            "1. Executive Summary\n"
            "2. Background & Objectives\n"
            "3. Key Findings & Detailed Analysis\n"
            "4. Risk & Strategic Considerations\n"
            "5. Actionable Recommendations & Next Steps"
        )
        report_content = self.llm.generate(prompt=prompt)

        title = f"MultiMind Intelligence Report: {topic.title()}"
        summary = f"Comprehensive executive assessment on {topic} prepared on {timestamp}."

        # Save to database
        saved_report = AnalyticsRepository.save_report(
            db=self.db,
            title=title,
            topic=topic,
            summary=summary,
            content=report_content,
            sources=sources or [],
            format="markdown",
        )

        return {
            "report_id": saved_report.id,
            "title": title,
            "topic": topic,
            "summary": summary,
            "content": report_content,
            "sources": sources or [],
            "created_at": saved_report.created_at.isoformat() if saved_report.created_at else None,
        }

    def export_pdf(self, title: str, content: str) -> bytes:
        """Exports report text to PDF bytes using reportlab."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas

            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=letter)
            width, height = letter

            # Title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, title[:60])

            # Body lines
            c.setFont("Helvetica", 10)
            y = height - 80
            for line in content.split("\n"):
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y = height - 50
                # Trim line length for page width
                clean_line = line.replace("*", "").replace("#", "").strip()
                if clean_line:
                    c.drawString(50, y, clean_line[:95])
                    y -= 14
                else:
                    y -= 8

            c.save()
            buf.seek(0)
            return buf.getvalue()
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            return f"PDF generation error: {e}".encode("utf-8")
