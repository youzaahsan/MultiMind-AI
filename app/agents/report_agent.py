from typing import Any, Dict
from app.agents.state import AgentState, ToolCallRecord
from app.agents.tools import ToolRegistry
from app.services.llm_service import LLMService

class ReportAgent:
    """Specialized agent for generating structured, multi-section executive reports."""

    def __init__(self, tools: ToolRegistry, llm: LLMService):
        self.tools = tools
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        query = state.resolved_query or state.user_query

        # Retrieve relevant context from documents
        search_res = self.tools.document_search(query=query, top_k=6)
        context = search_res.get("context", "")

        report_text = self.tools.generate_report(
            topic=query,
            context=context if context else "Synthesize standard domain methodology and findings.",
        )

        state.tool_calls.append(ToolCallRecord(
            tool_name="generate_report",
            arguments={"topic": query},
            output={"length_characters": len(report_text)},
        ))

        state.final_response = report_text
        state.sources = search_res.get("citations", [])
        return state
