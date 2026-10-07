import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.repositories import ConversationRepository
from app.agents.orchestrator import OrchestratorAgent
from app.agents.state import AgentState, AgentMessage
from app.utils.security import sanitize_prompt_input
from app.utils.logging import get_logger

logger = get_logger("routes_chat")
router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    document_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    active_agent: Optional[str] = None
    routing_reason: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)

@router.post("/chat", response_model=ChatResponse)
def chat_with_agent(payload: ChatRequest, db: Session = Depends(get_db)):
    """Conversational endpoint executing orchestrator routing, memory resolution, and specialized agents."""
    session_id = payload.session_id or str(uuid.uuid4())
    cleaned_query, is_suspicious = sanitize_prompt_input(payload.message)

    # 1. Fetch conversation history from database
    db_history = ConversationRepository.get_history(db, session_id=session_id, limit=20)
    history_messages = [
        AgentMessage(
            role=msg.role,
            content=msg.content,
            sources=msg.sources or [],
            tool_name=msg.agent_name,
        )
        for msg in db_history
    ]

    # 2. Build Agent State
    state = AgentState(
        session_id=session_id,
        user_query=cleaned_query,
        chat_history=history_messages,
        metadata={"document_id": payload.document_id} if payload.document_id else {},
    )

    # 3. Save User message to database
    ConversationRepository.add_message(
        db=db,
        session_id=session_id,
        role="user",
        content=payload.message,
    )

    # 4. Run Orchestrator
    orchestrator = OrchestratorAgent()
    final_state = orchestrator.route_and_execute(state)

    response_text = final_state.final_response or "I processed your request, but no output was generated."

    # 5. Save Assistant response to database
    ConversationRepository.add_message(
        db=db,
        session_id=session_id,
        role="assistant",
        content=response_text,
        sources=final_state.sources,
        agent_name=final_state.active_agent,
    )

    return {
        "session_id": session_id,
        "response": response_text,
        "sources": final_state.sources,
        "active_agent": final_state.active_agent,
        "routing_reason": final_state.routing_reason,
        "tool_calls": [t.model_dump() for t in final_state.tool_calls],
    }

@router.get("/conversation/{session_id}")
def get_conversation_history(session_id: str, db: Session = Depends(get_db)):
    """Retrieves chronological message history for a given conversation session."""
    messages = ConversationRepository.get_history(db, session_id=session_id)
    return {
        "session_id": session_id,
        "message_count": len(messages),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sources": m.sources,
                "agent_name": m.agent_name,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
    }
