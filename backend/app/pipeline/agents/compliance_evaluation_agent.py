from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from app.pipeline.state import NodeResult, NodeStatus, PipelineState

logger = logging.getLogger(__name__)

COMPLIANCE_EVALUATION_STAGE = "compliance_evaluation"


async def run_compliance_evaluation(
    state: PipelineState,
    session_factory: Any = None,
) -> PipelineState:
    logger.info("Pipeline: running compliance evaluation agent")
    state.current_node = COMPLIANCE_EVALUATION_STAGE
    start_time = time.monotonic()

    result = NodeResult(
        node=COMPLIANCE_EVALUATION_STAGE,
        status=NodeStatus.RUNNING,
        output={},
        started_at=datetime.now(UTC).isoformat(),
    )

    try:
        active_skills = state.metadata.get("active_skills", [])
        if not active_skills:
            logger.info("Compliance evaluation skipped: no active skills")
            result.status = NodeStatus.SKIPPED
            result.output = {"reason": "No active skills to evaluate"}
        elif not session_factory:
            logger.info("Compliance evaluation skipped: no session factory")
            result.status = NodeStatus.SKIPPED
            result.output = {"reason": "No session factory available"}
        else:
            from app.services.skill_compliance import ComplianceEvaluator

            content = state.final_content or state.draft_content
            if not content:
                logger.info("Compliance evaluation skipped: no content to evaluate")
                result.status = NodeStatus.SKIPPED
                result.output = {"reason": "No content available for evaluation"}
            else:
                evaluator = ComplianceEvaluator()
                compliance_results = []

                async with session_factory():
                    for skill in active_skills:
                        skill_id = skill.get("id", "")
                        skill_name = skill.get("name", "")
                        skill_content = skill.get("content_markdown", "")
                        skill_category = skill.get("category", "")

                        eval_result = await evaluator.evaluate(
                            content, skill_content, skill_category,
                        )
                        compliance_results.append({
                            "skill_id": skill_id,
                            "skill_name": skill_name,
                            "compliance_score": eval_result.get("compliance_score", 0.0),
                            "violations": eval_result.get("violations", []),
                        })

                state.metadata["compliance_results"] = compliance_results

                result.output = {
                    "evaluated_skills": len(compliance_results),
                    "average_compliance": (
                        sum(r["compliance_score"] for r in compliance_results) / len(compliance_results)
                        if compliance_results else 0.0
                    ),
                }
                result.status = NodeStatus.SUCCESS

    except Exception as e:
        logger.exception("Compliance evaluation failed: %s", e)
        result.status = NodeStatus.SKIPPED
        result.error = str(e)
        result.output = {"compliance_results": []}

    result.completed_at = datetime.now(UTC).isoformat()
    result.latency_ms = (time.monotonic() - start_time) * 1000
    state.add_node_result(COMPLIANCE_EVALUATION_STAGE, result)
    return state
