from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
import uuid

from app.utils.datetime_utils import utc_now

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=utc_now)

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
    agent_name: str = ""
    event_type: str
    status: str = "running"
    message: str = ""
    progress_percent: float = 0.0
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = ""

class AgentStatusUpdate(BaseModel):
    project_id: str
    active_agent: str
    current_task: str
    progress: float
    recent_logs: List[str] = []
    timestamp: datetime = Field(default_factory=utc_now)
