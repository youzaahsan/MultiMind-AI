from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AgentMessage(BaseModel):
    role: str  # user, assistant, system, tool
    content: str
    tool_name: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)

class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    output: Any
    status: str = "success"  # success, error

class AgentState(BaseModel):
    session_id: str
    user_query: str
    resolved_query: Optional[str] = None
    chat_history: List[AgentMessage] = Field(default_factory=list)
    active_agent: Optional[str] = None
    routing_reason: Optional[str] = None
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    retrieved_context: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    final_response: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
