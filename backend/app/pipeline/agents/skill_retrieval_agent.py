from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from app.pipeline.state import NodeResult, NodeStatus, PipelineState

logger = logging.getLogger(__name__)

SKILL_RETRIEVAL_STAGE = "skill_retrieval"


async def run_skill_retrieval(
    state: PipelineState,
    session_factory: Any = None,
) -> PipelineState:
    logger.info("Pipeline: running skill retrieval agent")
    state.current_node = SKILL_RETRIEVAL_STAGE
    start_time = time.monotonic()

    result = NodeResult(
        node=SKILL_RETRIEVAL_STAGE,
        status=NodeStatus.RUNNING,
        output={},
        started_at=datetime.now(UTC).isoformat(),
    )

    try:
        project_id = state.metadata.get("project_id", "")
        if not project_id or not session_factory:
            logger.info(
                "Skill retrieval skipped: no project_id or session factory"
            )
            result.status = NodeStatus.SKIPPED
            result.output = {"reason": "No project context available"}
        else:
            from app.services.skill_injection import SkillInjectionEngine

            async with session_factory() as session:
                engine = SkillInjectionEngine(session)
                active_package = await engine.build_active_skill_package(
                    project_id=project_id,
                    agent_name=state.current_node,
                )

                state.metadata["active_skills"] = active_package.get("active_skills", [])
                state.metadata["skill_priorities"] = active_package.get("skill_priorities", {})
                state.metadata["skill_conflicts"] = active_package.get("conflicts", [])

                ctx_parts = []
                for skill in active_package.get("active_skills", []):
                    ctx_parts.append(
                        f"=== Skill: {skill['name']} ({skill['category']}) ===\n{skill['content_markdown']}"
                    )
                state.metadata["skill_context"] = (
                    "\n\n".join(ctx_parts) if ctx_parts else "No active skills"
                )

                result.output = {
                    "active_skills_count": len(active_package.get("active_skills", [])),
                    "conflicts_count": len(active_package.get("conflicts", [])),
                }
                result.status = NodeStatus.SUCCESS

    except Exception as e:
        logger.exception("Skill retrieval failed: %s", e)
        result.status = NodeStatus.SKIPPED
        result.error = str(e)
        result.output = {
            "active_skills": [],
            "skill_priorities": {},
            "skill_conflicts": [],
        }

    result.completed_at = datetime.now(UTC).isoformat()
    result.latency_ms = (time.monotonic() - start_time) * 1000
    state.add_node_result(SKILL_RETRIEVAL_STAGE, result)
    return state
