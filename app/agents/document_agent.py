from typing import Any, Dict
from app.agents.state import AgentState, ToolCallRecord
from app.agents.tools import ToolRegistry
from app.services.llm_service import LLMService

class DocumentAgent:
    """Specialized agent for document summarization, comparisons, and structural extraction."""

    def __init__(self, tools: ToolRegistry, llm: LLMService):
        self.tools = tools
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        query = state.resolved_query or state.user_query
        
        # Check if comparing two documents
        if "compare" in query.lower():
            search_res = self.tools.document_search(query=query, top_k=6)
            state.tool_calls.append(ToolCallRecord(
                tool_name="document_search",
                arguments={"query": query, "top_k": 6},
                output={"matches": search_res["matches_count"]},
            ))
            context = search_res.get("context", "")
            prompt = (
                f"Compare the contents, methodology, and key distinctions from the documents below:\n\n{context}\n\n"
                f"User Request: {query}\n"
                "Provide a side-by-side comparison table or bulleted synthesis."
            )
            state.final_response = self.llm.generate(prompt=prompt)
            state.sources = search_res.get("citations", [])
            return state

        # Default: Summarization
        search_res = self.tools.document_search(query=query, top_k=4)
        state.tool_calls.append(ToolCallRecord(
            tool_name="summarize_document",
            arguments={"query": query},
            output={"context_length": len(search_res.get("context", ""))},
        ))
        context = search_res.get("context", "")
        summary = self.tools.summarize_document(context if context else query)
        state.final_response = summary
        state.sources = search_res.get("citations", [])
        return state
