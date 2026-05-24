import time
import uuid
from datetime import datetime

from langgraph.graph import StateGraph

from app.log_config.logger import get_logger
from app.engine.graph_state import create_initial_state, WorkflowState


class WorkflowExecutor:
    def __init__(self, graph: StateGraph):
        self.graph = graph
        self.logger = get_logger(self.__class__.__name__)

    async def execute(
        self,
        project_id: str,
        topic: str = "",
        title: str = "",
        content_type: str = "article",
        tone: str = "professional",
        points_to_cover: list[str] | None = None,
        target_audience: str = "",
        seo_keywords: list[str] | None = None,
        workflow_id: str | None = None,
    ) -> dict:
        wid = workflow_id or str(uuid.uuid4())
        start_time = time.time()

        initial = create_initial_state(
            project_id=project_id,
            topic=topic,
            title=title,
            content_type=content_type,
            tone=tone,
            points_to_cover=points_to_cover,
            target_audience=target_audience,
            seo_keywords=seo_keywords,
            workflow_id=wid,
        )
        initial["start_time"] = start_time

        config = {"configurable": {"thread_id": wid}}

        self.logger.info(f"Starting workflow {wid} for project {project_id}", extra={"topic": topic})

        try:
            final_state = await self.graph.ainvoke(initial, config=config)

            total_duration = time.time() - start_time
            telemetry = dict(final_state.get("telemetry", {}))
            telemetry["total_duration_ms"] = round(total_duration * 1000, 2)
            telemetry["total_retries"] = sum(
                1 for e in final_state.get("errors", []) if "retry" in str(e.get("error", "")).lower()
            )
            telemetry["total_sources"] = len(final_state.get("all_sources", []))
            telemetry["total_claims"] = len(final_state.get("claims", []))
            telemetry["total_contradictions"] = len(final_state.get("contradictions", []))
            telemetry["revision_count"] = final_state.get("revision_count", 0)
            telemetry["hyperlinks_checked"] = len(final_state.get("hyperlink_results", []))
            telemetry["hyperlinks_valid"] = sum(
                1 for h in final_state.get("hyperlink_results", []) if h.get("is_verified")
            )
            telemetry["overall_quality_score"] = self._compute_quality_score(final_state)
            final_state["telemetry"] = telemetry

            self.logger.info(
                f"Workflow {wid} completed in {total_duration:.2f}s",
                extra={"steps": len(final_state.get("steps_completed", [])), "errors": len(final_state.get("errors", []))},
            )

            return final_state

        except Exception as e:
            self.logger.error(f"Workflow {wid} failed: {e}")
            return {
                "workflow_id": wid,
                "project_id": project_id,
                "status": "failed",
                "error": str(e),
                "steps_completed": [],
                "all_sources": [],
                "claims": [],
                "verified_claims": [],
                "contradictions": [],
                "content_draft": {},
                "final_content": {},
                "audit_result": {},
                "hyperlink_results": [],
                "telemetry": {"total_duration_ms": round((time.time() - start_time) * 1000, 2)},
            }

    def _compute_quality_score(self, state: dict) -> float:
        score = 0.7
        if state.get("audit_result", {}).get("audit_passed"):
            score += 0.1
        if state.get("hyperlink_results"):
            valid = sum(1 for h in state["hyperlink_results"] if h.get("is_verified"))
            total = len(state["hyperlink_results"])
            if total > 0:
                score += 0.1 * (valid / total)
        if state.get("revision_count", 0) > 0:
            score += 0.05
        if state.get("contradictions"):
            score -= 0.05 * min(len(state["contradictions"]), 4)
        return max(0.0, min(1.0, score))
