from __future__ import annotations

import logging
from typing import Any, Coroutine
from app.agents.pipeline import PipelineStage, AgentInput
from app.domains.project.models import ProjectMemory
from app.services.embedding_service import EmbeddingService
from app.infrastructure.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)

class MemoryIngestionHook:
    """
    Pipeline hook that automatically converts agent outputs 
    into project memories for long-term intelligence.
    """
    def __init__(self, uow: UnitOfWork, embedding_service: EmbeddingService):
        self.uow = uow
        self.embedding_service = embedding_service

    async def __call__(
        self, 
        stage: PipelineStage, 
        agent_input: AgentInput, 
        stage_data: dict[str, Any] | None
    ) -> None:
        # We only ingest memories after successful execution and output parsing
        if stage != PipelineStage.EVENT_EMISSION or not stage_data:
            return

        project_id = agent_input.metadata.get("project_id")
        if not project_id:
            return

        output = stage_data.get("output")
        if not output:
            return

        try:
            # 1. Determine memory type based on agent
            agent_name = agent_input.agent_type.lower()
            memory_type = "general"
            if "research" in agent_name:
                memory_type = "research_finding"
            elif "fact" in agent_name:
                memory_type = "verified_fact"
            elif "writer" in agent_name:
                memory_type = "generated_content"
            elif "planner" in agent_name:
                memory_type = "project_decision"

            # 2. Convert output to string for embedding
            content = str(output) if not isinstance(output, str) else output
            
            # 3. Generate embedding
            vector = await self.embedding_service.generate_embedding(content)

            # 4. Store as ProjectMemory
            memory = ProjectMemory(
                project_id=project_id,
                memory_type=memory_type,
                content=content,
                embedding=vector,
                confidence_score=1.0 if "fact" in agent_name else 0.8
            )
            
            self.uow.projects.create(memory) # Using repository create
            await self.uow.commit()
            
            logger.info(f"Automatically ingested {memory_type} memory for project {project_id}")
            
        except Exception as e:
            logger.error(f"Automatic memory ingestion failed: {e}")
