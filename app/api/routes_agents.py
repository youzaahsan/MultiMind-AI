from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.agents.tools import get_tool_registry
from app.services.report_service import ReportService
from app.graph.graph_retriever import GraphRAGRetriever
from app.utils.logging import get_logger

logger = get_logger("routes_agents")
router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    top_k: int = 4
    document_id: Optional[str] = None
    use_graph: bool = True

class QuizRequest(BaseModel):
    topic_or_context: str
    num_questions: int = 5

class ReportRequest(BaseModel):
    topic: str
    context: Optional[str] = None

class ImageAnalysisRequest(BaseModel):
    image_path: str
    prompt: Optional[str] = None

@router.post("/search")
def search_knowledge(payload: SearchRequest):
    """Executes semantic search across ingested documents with optional GraphRAG entity retrieval."""
    if payload.use_graph:
        graph_retriever = GraphRAGRetriever()
        results = graph_retriever.retrieve_hybrid(query=payload.query, top_k=payload.top_k)
        return results
    else:
        tools = get_tool_registry()
        results = tools.document_search(
            query=payload.query,
            top_k=payload.top_k,
            document_id=payload.document_id,
        )
        return results

@router.post("/generate-quiz")
def generate_quiz(payload: QuizRequest):
    """Generates multiple choice questions (MCQs) and answer keys."""
    tools = get_tool_registry()
    quiz = tools.generate_quiz(
        topic_or_context=payload.topic_or_context,
        num_questions=payload.num_questions,
    )
    return {
        "topic": payload.topic_or_context[:100],
        "questions_count": payload.num_questions,
        "quiz": quiz,
    }

@router.post("/generate-report")
def generate_report(payload: ReportRequest, db: Session = Depends(get_db)):
    """Generates a structured comprehensive intelligence report and saves it to the database."""
    report_service = ReportService(db)
    result = report_service.generate_report(
        topic=payload.topic,
        context=payload.context,
    )
    return result

@router.post("/analyze-image")
def analyze_image(payload: ImageAnalysisRequest):
    """Analyzes an image file, extracting visual metrics, OCR text, and structural interpretation."""
    tools = get_tool_registry()
    try:
        res = tools.analyze_image(image_path=payload.image_path, prompt=payload.prompt)
        return res
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
