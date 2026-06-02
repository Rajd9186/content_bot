from __future__ import annotations

import logging
from typing import Any, Coroutine, Dict
from app.pipeline.state import PipelineState, NodeResult, NodeStatus
from app.services.context_assembly_engine import ContextAssemblyEngine
from app.services.embedding_service import EmbeddingService
from app.infrastructure.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)

class MemoryRetrievalAgent:
    """
    Intelligence node that retrieves relevant project memories 
    and augments the pipeline state with project context.
    """
    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self._embedding_service = EmbeddingService()
        self._context_engine = ContextAssemblyEngine(uow, self._embedding_service)

    async def execute(self, state: PipelineState) -> NodeResult:
        logger.info("Intelligence: Retrieving project context for %s", state.workflow_id)
        
        project_id = state.metadata.get("project_id")
        if not project_id:
            logger.warning("No project_id found in metadata, skipping memory retrieval")
            return NodeResult(
                node="memory_retrieval",
                status=NodeStatus.SUCCESS,
                output={"message": "No project context retrieved (no project_id)"},
                started_at=None, # will be set by pipeline if needed
                completed_at=None,
            )

        try:
            # Assemble augmented context
            context_package = await self._context_engine.assemble_context(
                project_id=project_id,
                user_prompt=state.prompt
            )
            
            # Store the assembled context in the state so subsequent agents can use it
            state.project_context = context_package
            
            return NodeResult(
                node="memory_retrieval",
                status=NodeStatus.SUCCESS,
                output={
                    "memories_retrieved": len(context_package["semantic_memories"]),
                    "pinned_knowledge_count": len(context_package["pinned_knowledge"]),
                    "context_assembled": True
                },
            )
        except Exception as e:
            logger.error("Memory retrieval failed: %s", e, exc_info=True)
            return NodeResult(
                node="memory_retrieval",
                status=NodeStatus.FAILED,
                error=str(e),
            )
