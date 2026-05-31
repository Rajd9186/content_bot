from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from app.pipeline.state import NodeResult, NodeStatus, PipelineState

logger = logging.getLogger(__name__)

MEMORY_RETRIEVAL_STAGE = "memory_retrieval"


async def run_memory_retrieval(
    state: PipelineState,
    session_factory: Any = None,
) -> PipelineState:
    logger.info("Pipeline: running memory retrieval agent")
    state.current_node = MEMORY_RETRIEVAL_STAGE
    start_time = time.monotonic()

    result = NodeResult(
        node=MEMORY_RETRIEVAL_STAGE,
        status=NodeStatus.RUNNING,
        output={},
        started_at=datetime.now(UTC).isoformat(),
    )

    try:
        project_id = state.metadata.get("project_id", "")
        if not project_id or not session_factory:
            logger.info(
                "Memory retrieval skipped: no project_id or session factory"
            )
            result.status = NodeStatus.SKIPPED
            result.output = {"reason": "No project context available"}
        else:
            from app.services.context_assembly import ContextAssemblyEngine
            from app.services.retrieval_metrics import retrieval_metrics

            async with session_factory() as session:
                engine = ContextAssemblyEngine(session)
                context = await engine.assemble(
                    project_id=project_id,
                    prompt=state.topic,
                    top_k=10,
                    similarity_threshold=0.0,
                )

                latency = (time.monotonic() - start_time) * 1000
                retrieval_metrics.record_retrieval(
                    project_id=project_id,
                    query=state.topic,
                    latency_ms=latency,
                    results_count=len(context.get("relevant_memories", [])),
                )

                for mem in context.get("relevant_memories", []):
                    retrieval_metrics.record_memory_usage(mem["id"])

                state.metadata["project_context"] = context.get("project_context", {})
                state.metadata["relevant_memories"] = context.get("relevant_memories", [])
                state.metadata["pinned_memories"] = context.get("pinned_memories", [])

                if context.get("project_context", {}).get("pinned_knowledge"):
                    pin_text = "\n".join(
                        f"- [{p['type']}] {p['content']}"
                        for p in context["project_context"]["pinned_knowledge"]
                    )
                    state.metadata["memory_context"] = (
                        "Project context retrieved. "
                        f"Pinned knowledge: {pin_text}"
                    )
                else:
                    state.metadata["memory_context"] = "No project context available"

                result.output = {
                    "relevant_memories": context.get("relevant_memories", []),
                    "related_outputs": context.get("related_outputs", []),
                    "related_prompts": context.get("related_prompts", []),
                    "memory_count": len(context.get("relevant_memories", [])),
                }
                result.status = NodeStatus.SUCCESS

    except Exception as e:
        logger.exception("Memory retrieval failed: %s", e)
        result.status = NodeStatus.SKIPPED
        result.error = str(e)
        result.output = {
            "relevant_memories": [],
            "related_outputs": [],
            "related_prompts": [],
        }

    result.completed_at = datetime.now(UTC).isoformat()
    result.latency_ms = (time.monotonic() - start_time) * 1000
    state.add_node_result(MEMORY_RETRIEVAL_STAGE, result)
    return state
