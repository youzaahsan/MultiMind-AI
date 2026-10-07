import ast
import operator
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import pandas as pd

from app.rag.retriever import RAGRetriever
from app.rag.vector_store import get_vector_store
from app.multimodal.image_processor import ImageProcessor
from app.multimodal.csv_processor import CSVProcessor
from app.multimodal.excel_processor import ExcelProcessor
from app.business_intelligence.kpis import KPICalculator
from app.business_intelligence.analytics import BusinessAnalytics
from app.business_intelligence.insights import BIInsightGenerator
from app.forecasting.inference import TimeSeriesForecaster
from app.services.llm_service import get_llm_service
from app.utils.logging import get_logger

logger = get_logger("agent_tools")

# Safe AST operator mapping for calculator
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def safe_eval_math(node: ast.AST) -> float:
    """Safely evaluates an arithmetic AST node without dynamic code execution."""
    if isinstance(node, ast.Expression):
        return safe_eval_math(node.body)
    elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    elif isinstance(node, ast.BinOp):
        left = safe_eval_math(node.left)
        right = safe_eval_math(node.right)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported mathematical operator: {op_type.__name__}")
    elif isinstance(node, ast.UnaryOp):
        operand = safe_eval_math(node.operand)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
    else:
        raise ValueError("Expression contains disallowed syntax or operations.")


class ToolRegistry:
    """Registry of verified, secure agent tools."""

    def __init__(self):
        self.retriever = RAGRetriever()
        self.llm = get_llm_service()
        self.forecaster = TimeSeriesForecaster()

    # Tool 1: document_search / semantic_search
    def document_search(self, query: str, top_k: int = 4, document_id: Optional[str] = None) -> Dict[str, Any]:
        """Searches ingested documents and returns matching chunks with citations."""
        matches, context = self.retriever.retrieve(query=query, top_k=top_k, document_id=document_id)
        citations = []
        for m in matches:
            meta = m.get("metadata", {})
            citations.append({
                "filename": meta.get("filename", "unknown"),
                "page": meta.get("page", 1),
                "section": meta.get("section", "General"),
                "score": m.get("rerank_score", m.get("score")),
            })
        return {
            "query": query,
            "matches_count": len(matches),
            "citations": citations,
            "context": context,
        }

    # Tool 2: summarize_document
    def summarize_document(self, text_or_context: str) -> str:
        """Generates an executive summary of provided document text."""
        prompt = f"Summarize the following document content clearly and concisely:\n\n{text_or_context}"
        return self.llm.generate(prompt=prompt)

    # Tool 3: analyze_image
    def analyze_image(self, image_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """Extracts visual metrics, aspect ratio, luminance, and analyzes image/chart content."""
        proc = ImageProcessor(image_path)
        extracted = proc.extract()
        analysis = self.llm.generate(
            prompt=prompt or "Analyze this image, chart, or technical diagram in detail.",
            image_base64=extracted.get("base64_data"),
        )
        return {
            "metadata": extracted.get("metadata"),
            "ocr_text": extracted.get("ocr_text"),
            "analysis": analysis,
        }

    # Tool 4: analyze_csv
    def analyze_csv(self, file_path: str) -> Dict[str, Any]:
        """Loads and calculates statistical metrics and summaries on CSV files."""
        proc = CSVProcessor(file_path)
        extracted = proc.extract()
        return {
            "metadata": extracted.get("metadata"),
            "statistics": extracted.get("statistics"),
            "missing_values": extracted.get("missing_percentages"),
            "sample_rows": extracted.get("sample_rows"),
            "summary_text": extracted.get("full_text"),
        }

    # Tool 5: analyze_excel
    def analyze_excel(self, file_path: str) -> Dict[str, Any]:
        """Analyzes Excel spreadsheets, multiple sheets, and formula definitions."""
        proc = ExcelProcessor(file_path)
        extracted = proc.extract()
        return {
            "metadata": extracted.get("metadata"),
            "sheets": extracted.get("sheets"),
            "summary_text": extracted.get("full_text"),
        }

    # Tool 6: calculator
    def calculator(self, expression: str) -> Dict[str, Any]:
        """Safely evaluates arithmetic expressions (addition, subtraction, multiplication, division, powers)."""
        clean_expr = expression.strip().replace("^", "**")
        try:
            parsed = ast.parse(clean_expr, mode="eval")
            result = safe_eval_math(parsed)
            return {
                "expression": expression,
                "result": round(result, 6),
                "status": "success",
            }
        except Exception as e:
            return {
                "expression": expression,
                "error": f"Mathematical evaluation error: {str(e)}",
                "status": "error",
            }

    # Tool 7: generate_quiz
    def generate_quiz(self, topic_or_context: str, num_questions: int = 5) -> str:
        """Generates multiple choice questions (MCQs) and answer keys from document context."""
        prompt = f"Create {num_questions} MCQs from the following text:\n\n{topic_or_context}"
        return self.llm.generate(prompt=prompt)

    # Tool 8: generate_report
    def generate_report(self, topic: str, context: str) -> str:
        """Generates a structured research/intelligence report."""
        prompt = (
            f"Generate a comprehensive structured report on '{topic}' based on this context:\n\n{context}"
        )
        return self.llm.generate(prompt=prompt)

    # Tool 9: business_analysis
    def business_analysis(self, df: pd.DataFrame, revenue_col: Optional[str] = None, cost_col: Optional[str] = None) -> Dict[str, Any]:
        """Calculates core financial KPIs, margins, and operational insights."""
        kpis = KPICalculator.calculate_core_kpis(df, revenue_col=revenue_col, cost_col=cost_col)
        # Try to find a dimension column (product or category)
        dim_col = None
        for c in df.columns:
            if c.lower() in ["product", "item", "category", "region"]:
                dim_col = c
                break
        rev_col = kpis.get("revenue_column")
        dimensions = []
        if dim_col and rev_col:
            dimensions = BusinessAnalytics.analyze_dimensions(df, rev_col, dim_col)

        insights = BIInsightGenerator.generate_insights(kpis, dimensions)
        return {
            "kpis": kpis,
            "dimensions": dimensions,
            "insights": insights,
        }

    # Tool 10: forecasting
    def forecasting(
        self,
        df: pd.DataFrame,
        date_column: str,
        target_column: str,
        horizon_periods: int = 7,
    ) -> Dict[str, Any]:
        """Performs time series forecasting with out-of-sample metrics."""
        return self.forecaster.forecast(
            df=df,
            date_column=date_column,
            target_column=target_column,
            horizon_periods=horizon_periods,
        )


_tool_registry_instance: Optional[ToolRegistry] = None

def get_tool_registry() -> ToolRegistry:
    global _tool_registry_instance
    if _tool_registry_instance is None:
        _tool_registry_instance = ToolRegistry()
    return _tool_registry_instance
