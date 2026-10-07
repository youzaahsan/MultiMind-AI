from pathlib import Path
from typing import Any, Dict
import pandas as pd
from app.agents.state import AgentState, ToolCallRecord
from app.agents.tools import ToolRegistry
from app.services.llm_service import LLMService
from app.config.settings import settings

class DataAgent:
    """Specialized agent for tabular datasets, CSV/Excel profiling, and statistical reasoning."""

    def __init__(self, tools: ToolRegistry, llm: LLMService):
        self.tools = tools
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        query = state.resolved_query or state.user_query

        # Find latest CSV or Excel file if not specified
        file_path = state.metadata.get("file_path")
        if not file_path or not Path(file_path).exists():
            data_files = list(settings.UPLOAD_DIR.glob("*.csv")) + list(settings.UPLOAD_DIR.glob("*.xlsx"))
            if data_files:
                file_path = str(data_files[-1])

        if file_path and Path(file_path).exists():
            p = Path(file_path)
            if p.suffix.lower() == ".csv":
                res = self.tools.analyze_csv(file_path)
                tool_name = "analyze_csv"
            else:
                res = self.tools.analyze_excel(file_path)
                tool_name = "analyze_excel"

            state.tool_calls.append(ToolCallRecord(
                tool_name=tool_name,
                arguments={"file": p.name},
                output={"rows": res["metadata"].get("rows"), "columns": res["metadata"].get("columns_count")},
            ))

            prompt = (
                f"User Question on Dataset: {query}\n\n"
                f"Dataset Summary & Statistics:\n{res.get('summary_text')}\n\n"
                "Answer the user query accurately with numerical facts and findings from the dataset."
            )
            state.final_response = self.llm.generate(prompt=prompt)
            state.sources = [{"filename": p.name, "page": 1, "section": "Tabular Data"}]
        else:
            state.final_response = (
                "Please upload a CSV or Excel dataset to perform statistical data analysis and table inspection."
            )

        return state
