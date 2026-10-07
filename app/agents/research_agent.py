from typing import Any, Dict
from app.agents.state import AgentState, ToolCallRecord
from app.agents.tools import ToolRegistry
from app.services.llm_service import LLMService

class ResearchAgent:
    """Specialized agent for searching, retrieving, and verifying knowledge from vector and graph stores."""

    def __init__(self, tools: ToolRegistry, llm: LLMService):
        self.tools = tools
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        query = state.resolved_query or state.user_query
        search_res = self.tools.document_search(query=query, top_k=4)

        state.tool_calls.append(ToolCallRecord(
            tool_name="document_search",
            arguments={"query": query, "top_k": 4},
            output={"matches": search_res["matches_count"], "citations": search_res["citations"]},
        ))

        state.retrieved_context = search_res["context"]
        state.sources = search_res["citations"]

        # Prompt LLM with retrieved context
        from app.rag.prompts import RAG_PROMPT_TEMPLATE, SYSTEM_RAG_PROMPT
        formatted_prompt = RAG_PROMPT_TEMPLATE.format(
            context=search_res["context"] if search_res["context"] else "No matching documents found in database.",
            question=query,
        )

        response = self.llm.generate(prompt=formatted_prompt, system_prompt=SYSTEM_RAG_PROMPT)
        state.final_response = response
        return state
