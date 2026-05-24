from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
import uuid

class ChatMessage(BaseModel):
    role: str # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

class ChatToolCall(BaseModel):
    tool: str
    parameters: Dict[str, Any]

class ChatResponse(BaseModel):
    content: str
    project_id: str
    tool_calls: List[ChatToolCall] = []
    metadata: Dict[str, Any] = {}

class WorkflowEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    workflow_id: Optional[str] = None
    node_name: str
    event_type: str # 'info', 'discovery', 'claim', 'contradiction', 'warning', 'error'
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AgentStatusUpdate(BaseModel):
    project_id: str
    active_agent: str
    current_task: str
    progress: float
    recent_logs: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
