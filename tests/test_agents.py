import pytest
from app.agents.orchestrator import OrchestratorAgent
from app.agents.state import AgentState, AgentMessage
from app.agents.tools import ToolRegistry, safe_eval_math
import ast

def test_safe_eval_math():
    node = ast.parse("10 * (5 + 3) / 2 - 4", mode="eval")
    res = safe_eval_math(node)
    assert res == 36.0

def test_safe_eval_math_rejects_code_execution():
    with pytest.raises(Exception):
        node = ast.parse("__import__('os').system('ls')", mode="eval")
        safe_eval_math(node)

def test_orchestrator_routing():
    orchestrator = OrchestratorAgent()

    # Quiz routing
    state_quiz = AgentState(session_id="s1", user_query="Create 20 MCQs from Chapter 3")
    final_quiz = orchestrator.route_and_execute(state_quiz)
    assert final_quiz.active_agent == "quiz_agent"

    # Vision routing
    state_vision = AgentState(session_id="s2", user_query="Explain this diagram and system architecture")
    final_vision = orchestrator.route_and_execute(state_vision)
    assert final_vision.active_agent == "vision_agent"

    # Math routing
    state_math = AgentState(session_id="s3", user_query="150 * 4 + 25")
    final_math = orchestrator.route_and_execute(state_math)
    assert final_math.active_agent == "calculator"
    assert "625" in final_math.final_response

def test_conversation_memory_coreference():
    orchestrator = OrchestratorAgent()
    history = [
        AgentMessage(role="user", content="What is supervised learning?"),
        AgentMessage(role="assistant", content="Supervised learning uses labeled training data."),
    ]
    state = AgentState(
        session_id="s4",
        user_query="What are its advantages?",
        chat_history=history,
    )
    final_state = orchestrator.route_and_execute(state)
    assert "supervised learning" in final_state.resolved_query.lower()
