import re
from typing import Any, Dict, List, Optional
from app.agents.state import AgentState, AgentMessage, ToolCallRecord
from app.agents.tools import ToolRegistry, get_tool_registry
from app.agents.research_agent import ResearchAgent
from app.agents.document_agent import DocumentAgent
from app.agents.vision_agent import VisionAgent
from app.agents.data_agent import DataAgent
from app.agents.quiz_agent import QuizAgent
from app.agents.report_agent import ReportAgent
from app.agents.bi_agent import BusinessIntelligenceAgent
from app.agents.forecasting_agent import ForecastingAgent
from app.services.llm_service import get_llm_service
from app.utils.logging import get_logger

logger = get_logger("orchestrator")

class OrchestratorAgent:
    """
    Central Orchestrator:
    - Resolves conversational memory and coreferences (e.g. 'its advantages')
    - Analyzes intent and routes queries to specialized agents
    - Coordinates execution trace, tool calls, and structured response synthesis
    """

    def __init__(self, tools: Optional[ToolRegistry] = None):
        self.tools = tools or get_tool_registry()
        self.llm = get_llm_service()

        # Instantiate specialized agents
        self.research_agent = ResearchAgent(self.tools, self.llm)
        self.document_agent = DocumentAgent(self.tools, self.llm)
        self.vision_agent = VisionAgent(self.tools, self.llm)
        self.data_agent = DataAgent(self.tools, self.llm)
        self.quiz_agent = QuizAgent(self.tools, self.llm)
        self.report_agent = ReportAgent(self.tools, self.llm)
        self.bi_agent = BusinessIntelligenceAgent(self.tools)
        self.forecasting_agent = ForecastingAgent(self.tools)

    def route_and_execute(self, state: AgentState) -> AgentState:
        """Main orchestrator lifecycle."""
        # 1. Resolve coreference with conversation memory
        resolved_query = self._resolve_coreferences(state.user_query, state.chat_history)
        state.resolved_query = resolved_query

        # 2. Check for arithmetic calculation
        math_expr = self._extract_math_expression(state.user_query)
        if math_expr:
            calc_res = self.tools.calculator(math_expr)
            state.active_agent = "calculator"
            state.tool_calls.append(ToolCallRecord(
                tool_name="calculator",
                arguments={"expression": math_expr},
                output=calc_res,
            ))
            if "error" in calc_res:
                state.final_response = calc_res["error"]
            else:
                state.final_response = f"Calculation Result: **{calc_res['result']}**"
            return state

        # 3. Classify intent & route to specialized agent
        agent_name, routing_reason = self._classify_intent(resolved_query)
        state.active_agent = agent_name
        state.routing_reason = routing_reason
        logger.info(f"Routed query '{resolved_query[:60]}' to [{agent_name}] because: {routing_reason}")

        # 4. Delegate to the specialized agent
        if agent_name == "quiz_agent":
            state = self.quiz_agent.run(state)
        elif agent_name == "vision_agent":
            state = self.vision_agent.run(state)
        elif agent_name == "forecasting_agent":
            state = self.forecasting_agent.run(state)
        elif agent_name == "bi_agent":
            state = self.bi_agent.run(state)
        elif agent_name == "data_agent":
            state = self.data_agent.run(state)
        elif agent_name == "report_agent":
            state = self.report_agent.run(state)
        elif agent_name == "document_agent":
            state = self.document_agent.run(state)
        else:
            state = self.research_agent.run(state)

        return state

    def _resolve_coreferences(self, query: str, history: List[AgentMessage]) -> str:
        """
        Resolves ambiguous pronouns ('its', 'their', 'this', 'it') by substituting
        the dominant subject of the preceding conversation turn.
        """
        if not history:
            return query

        query_lower = query.lower()
        pronouns = ["its", "their", "it", "this", "these"]

        # Check if query starts with or relies on pronoun
        has_pronoun = any(re.search(rf"\b{p}\b", query_lower) for p in pronouns)
        if not has_pronoun:
            return query

        # Find the last user turn and assistant turn
        last_user_msg = next((m.content for m in reversed(history) if m.role == "user"), None)
        if not last_user_msg:
            return query

        # Extract core subject (e.g. "What is supervised learning?" -> "supervised learning")
        cleaned_last = re.sub(r"(?i)^(what is|explain|tell me about|how does|what are)\s+", "", last_user_msg).strip(" ?.")

        # Substitute pronoun
        resolved = query
        for p in ["its", "their"]:
            resolved = re.sub(rf"\b{p}\b", f"{cleaned_last}'s", resolved, flags=re.I)
        for p in ["it", "this"]:
            resolved = re.sub(rf"\b{p}\b", cleaned_last, resolved, flags=re.I)

        logger.info(f"Coreference resolved: '{query}' -> '{resolved}'")
        return resolved

    def _classify_intent(self, query: str) -> tuple[str, str]:
        """Classifies user intent using deterministic keyword & semantic pattern matching."""
        q = query.lower()

        # Quiz & Assessment
        if any(k in q for k in ["quiz", "mcq", "multiple choice", "questions from", "create questions"]):
            return "quiz_agent", "Query requests assessment/quiz generation."

        # Vision & Diagrams
        if any(k in q for k in ["diagram", "image", "chart image", "screenshot", "visual", "picture", "photo"]):
            return "vision_agent", "Query involves visual asset or diagram interpretation."

        # Forecasting
        if any(k in q for k in ["forecast", "predict next", "future sales", "demand projection", "time series"]):
            return "forecasting_agent", "Query requests predictive modeling or time series forecasting."

        # Business Intelligence & Financial KPIs
        if any(k in q for k in ["kpi", "profit margin", "gross profit", "revenue and cost", "sales growth", "aov", "average order value"]):
            return "bi_agent", "Query involves financial KPIs, profit calculations, or commercial insights."

        # Data Analysis & Excel / CSV Profiling
        if any(k in q for k in ["excel", "csv", "dataset", "highest revenue", "top product", "statistics", "missing values", "filter rows"]):
            return "data_agent", "Query targets tabular data analysis or column metrics."

        # Structured Reports
        if any(k in q for k in ["generate report", "create report", "intelligence report", "executive report"]):
            return "report_agent", "Query requests formal structured report generation."

        # Document Summarization & Comparison
        if any(k in q for k in ["summarize", "summary of", "compare these", "contrast documents", "overview of document"]):
            return "document_agent", "Query focuses on document-level summarization or comparison."

        # Default: Research & RAG Knowledge Search
        return "research_agent", "Query involves general information retrieval and document QA."

    def _extract_math_expression(self, text: str) -> Optional[str]:
        """Extracts arithmetic statements like '25 * 40' or 'What is 100 / 4?'."""
        clean = text.strip().rstrip("?").strip()
        # Remove common prefixes
        prefix_pattern = r"^(?:what is|calculate|solve|evaluate|compute)\s+"
        clean = re.sub(prefix_pattern, "", clean, flags=re.IGNORECASE).strip()

        # Must contain numbers and operators without letters
        if re.match(r"^[\d\s\+\-\*\/\%\^\(\)\.]+$", clean) and any(op in clean for op in ["+", "-", "*", "/", "%", "^"]):
            # Must contain at least one digit
            if any(c.isdigit() for c in clean):
                return clean
        return None
