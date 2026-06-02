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
                state.metadata["enhanced_prompt"] = context.get("prompt", state.topic)

                project_ctx = context.get("project_context", {})
                pinned_knowledge = project_ctx.get("pinned_knowledge", [])
                relevant_mems = project_ctx.get("relevant_memories", [])

                ctx_parts = []
                if pinned_knowledge:
                    ctx_parts.append("Pinned Knowledge:")
                    ctx_parts.extend(
                        f"- [{p['type']}] {p['content']}"
                        for p in pinned_knowledge
                    )
                if relevant_mems:
                    ctx_parts.append("Relevant Past Research:")
                    ctx_parts.extend(
                        f"- [{m['type']}] {m['content'][:300]}"
                        for m in relevant_mems[:5]
                    )
                related = project_ctx.get("related_outputs", [])
                if related:
                    ctx_parts.append("Related Previous Outputs:")
                    ctx_parts.extend(
                        f"- {r.get('title', 'Untitled')}"
                        for r in related[:3]
                    )

                state.metadata["memory_context"] = (
                    "\n".join(ctx_parts) if ctx_parts else "No project context available"
                )

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
