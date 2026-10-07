import re
from typing import Any, Dict
from app.agents.state import AgentState, ToolCallRecord
from app.agents.tools import ToolRegistry
from app.services.llm_service import LLMService

class QuizAgent:
    """Specialized agent for generating Multiple Choice Questions (MCQs), flashcards, and quizzes from ingested documents."""

    def __init__(self, tools: ToolRegistry, llm: LLMService):
        self.tools = tools
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        query = state.resolved_query or state.user_query

        # Determine requested number of questions
        count_match = re.search(r"(\d+)\s*(?:mcq|question|quiz)", query, re.I)
        num_q = int(count_match.group(1)) if count_match else 5
        num_q = min(num_q, 20)

        # Retrieve relevant context from documents
        search_res = self.tools.document_search(query=query, top_k=4)
        context = search_res.get("context", "")

        quiz_text = self.tools.generate_quiz(
            topic_or_context=context if context else query,
            num_questions=num_q,
        )

        state.tool_calls.append(ToolCallRecord(
            tool_name="generate_quiz",
            arguments={"query": query, "num_questions": num_q},
            output={"questions_generated": num_q},
        ))

        state.final_response = quiz_text
        state.sources = search_res.get("citations", [])
        return state
