from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from app.log_config.logger import get_logger
from app.repositories.project import ProjectRepository
from app.repositories.content import ContentRepository
from app.repositories.claim import ClaimRepository
from app.repositories.evidence import EvidenceRepository
from app.repositories.source import SourceRepository
from app.repositories.chat import WorkflowEventRepository
from app.repositories.contradiction import ContradictionRepository
from app.repositories.workflow import WorkflowExecutionRepository
from app.schemas.chat import ChatMessage, ChatResponse, ChatToolCall

class ResearchCopilotService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(self.__class__.__name__)
        
        # Repositories
        self.project_repo = ProjectRepository(session)
        self.content_repo = ContentRepository(session)
        self.claim_repo = ClaimRepository(session)
        self.evidence_repo = EvidenceRepository(session)
        self.source_repo = SourceRepository(session)
        self.event_repo = WorkflowEventRepository(session)
        self.contradiction_repo = ContradictionRepository(session)
        self.workflow_repo = WorkflowExecutionRepository(session)

    async def get_context(self, project_id: str) -> str:
        """Gather context from all project data to feed into the chatbot"""
        p_id = uuid.UUID(project_id)
        project = await self.project_repo.get(p_id)
        content = await self.content_repo.get_latest_by_project(p_id)
        claims = await self.claim_repo.get_by_project(p_id)
        contradictions = await self.contradiction_repo.get_by_project(p_id)
        
        context = f"Project: {project.title}\nTopic: {project.topic}\nStatus: {project.status}\n\n"
        
        if content:
            context += f"Latest Content Summary: {content.summary}\n"
            context += f"Word Count: {content.word_count}\n"
            context += f"Confidence Score: {content.overall_confidence}\n\n"
            
        context += f"Verified Claims Count: {len(claims)}\n"
        context += f"Contradictions Found: {len(contradictions)}\n"
        
        return context

    async def chat(self, project_id: str, message: str, history: List[ChatMessage]) -> ChatResponse:
        """Handle chatbot conversation logic"""
        context = await self.get_context(project_id)
        
        # In a real implementation, we would call an LLM here with the context and history.
        # For now, we simulate the intent recognition and response generation.
        
        msg_lower = message.lower()
        response_text = ""
        tool_calls = []
        
        # Simulate LLM tool selection and response generation based on keywords
        if "regenerate" in msg_lower or "re-run" in msg_lower:
            response_text = "I'm starting a new generation workflow for this project to refine the content based on your request."
            tool_calls.append(ChatToolCall(tool="trigger_workflow", parameters={"project_id": project_id, "mode": "v2"}))
        
        elif "contradiction" in msg_lower or "conflict" in msg_lower:
            conts = await self.contradiction_repo.get_by_project(uuid.UUID(project_id))
            if conts:
                response_text = f"I found {len(conts)} contradictions in the research. The most significant one is: '{conts[0].explanation}'."
            else:
                response_text = "I haven't detected any contradictions in the research data so far."
                
        elif "source" in msg_lower or "cite" in msg_lower or "citation" in msg_lower:
            sources = await self.source_repo.get_by_project(uuid.UUID(project_id))
            top_sources = ", ".join([s.domain for s in sources[:3]]) if sources else "no sources yet"
            response_text = f"The research is backed by {len(sources)} sources. Top domains include: {top_sources}."
            
        elif "claim" in msg_lower or "verify" in msg_lower:
            claims = await self.claim_repo.get_by_project(uuid.UUID(project_id))
            verified = [c for c in claims if c.status == "verified"]
            response_text = f"I've extracted {len(claims)} claims, of which {len(verified)} are fully verified by evidence."

        elif "status" in msg_lower or "running" in msg_lower or "doing" in msg_lower:
            wf = await self.workflow_repo.get_latest_by_project(uuid.UUID(project_id))
            if wf:
                response_text = f"The current workflow is in the '{wf.status}' state. The active node is '{wf.current_node}'."
            else:
                response_text = "There is no active workflow for this project right now."

        else:
            # Default response
            response_text = f"I'm your Research Copilot for the '{project_id}' project. I can help you investigate evidence, find contradictions, or control the research agents. What would you like to know about the current findings?"

        return ChatResponse(
            content=response_text,
            project_id=project_id,
            tool_calls=tool_calls,
            metadata={"timestamp": datetime.utcnow().isoformat()}
        )

    async def get_events(self, project_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent workflow events for live visualization"""
        events = await self.event_repo.get_by_project(project_id, limit=limit)
        return [
            {
                "id": str(e.id),
                "node_name": e.node_name,
                "event_type": e.event_type,
                "message": e.message,
                "data": e.data,
                "timestamp": e.timestamp.isoformat()
            }
            for e in events
        ]
