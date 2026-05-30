from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.infrastructure.messaging.redis_client import redis_client
from app.infrastructure.sse.manager import sse_manager
from app.infrastructure.unit_of_work import UnitOfWork
from app.pipeline.graph import pipeline
from app.pipeline.state import (
    HumanReview,
    PipelineState,
    ReviewAction,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["content-pipeline"])

_memory_fallback: dict[str, PipelineState] = {}


async def _load_state(workflow_id: str, db: AsyncSession) -> PipelineState | None:
    if db:
        try:
            uow = UnitOfWork(db)
            pipeline_run = await uow.pipelines.get_by_workflow_id(workflow_id)
            if pipeline_run:
                return uow.pipelines.to_pipeline_state(pipeline_run)
        except Exception:
            pass
    return _memory_fallback.get(workflow_id)


async def _save_state(state: PipelineState, db: AsyncSession) -> bool:
    if db:
        try:
            uow = UnitOfWork(db)
            await uow.pipelines.save_pipeline_state(state)
            await uow.commit()
            return True
        except Exception as e:
            with contextlib.suppress(Exception):
                await uow.rollback()
            logger.warning("DB persistence failed, using memory fallback: %s", e)
    _memory_fallback[state.workflow_id] = state
    return False


def _state_to_response(state: PipelineState) -> dict[str, Any]:
    return {
        "workflow_id": state.workflow_id,
        "workspace_id": state.workspace_id,
        "topic": state.topic,
        "current_node": state.current_node,
        "status": "completed" if state.all_nodes_completed() else "running",
        "has_failures": state.has_failures(),
        "draft_preview": state.draft_content[:500] if state.draft_content else "",
        "final_content": state.final_content[:500] if state.final_content else "",
        "needs_review": state.human_review is None and "human_review" in state.node_results,
        "review": state.human_review.model_dump() if state.human_review else None,
        "nodes": {
            k: {
                "node": k,
                "status": v.status.value,
                "error": v.error,
                "tokens_used": v.tokens_used,
                "latency_ms": v.latency_ms,
            }
            for k, v in state.node_results.items()
        },
        "research_summary": state.research_data.get("summary", "")[:300] if state.research_data else "",
        "seo_keywords": state.seo_metadata.get("primary_keywords", [])[:5] if state.seo_metadata else [],
        "error_count": len(state.errors),
        "created_at": state.created_at,
        "updated_at": state.updated_at,
    }


@router.post(
    "/pipeline/start",
    summary="Start a new content generation pipeline",
    operation_id="startPipeline",
    status_code=status.HTTP_201_CREATED,
)
async def start_pipeline(
    topic: str = Query(..., min_length=3, description="Content topic"),
    audience: str = Query("general", description="Target audience"),
    tone: str = Query("professional", description="Writing tone"),
    goals: str = Query("", description="Content goals"),
    workspace_id: str = Query("default", description="Workspace ID"),
    correlation_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    workflow_id = str(uuid4())
    corr_id = correlation_id or str(uuid4())

    state = PipelineState(
        workflow_id=workflow_id,
        workspace_id=workspace_id,
        correlation_id=corr_id,
        topic=topic,
        audience=audience,
        tone=tone,
        goals=goals,
        created_at=datetime.now(UTC).isoformat(),
    )

    await _save_state(state, db)

    logger.info("Pipeline started: workflow=%s topic=%s", workflow_id, topic)

    return JSONResponse(
        status_code=201,
        content={
            "workflow_id": workflow_id,
            "correlation_id": corr_id,
            "topic": topic,
            "status": "created",
            "message": "Pipeline created. Use POST /pipeline/{id}/run to execute.",
        },
    )


@router.post(
    "/pipeline/{workflow_id}/run",
    summary="Execute the content generation pipeline",
    operation_id="runPipeline",
)
async def run_pipeline(
    workflow_id: str,
    skip_review: bool = Query(False, description="Skip human review stage"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    state = await _load_state(workflow_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Broadcast initial running state
    await sse_manager.broadcast_pipeline_event(
        workflow_id, "pipeline_started", status="running"
    )

    if redis_client._client is not None:
        from app.infrastructure.workers.pipeline_worker import pipeline_worker
        await pipeline_worker.enqueue(workflow_id, skip_human_review=skip_review)
        return JSONResponse(content={
            "workflow_id": workflow_id,
            "status": "queued",
            "message": "Pipeline execution queued. Connect to /pipeline/{id}/events for live updates.",
        })
    else:
        try:
            state = await pipeline.execute(state, skip_human_review=skip_review)
            await _save_state(state, db)
            return JSONResponse(content=_state_to_response(state))
        except Exception as e:
            logger.exception("Pipeline execution failed for %s", workflow_id)
            state.errors.append(str(e))
            await _save_state(state, db)
            return JSONResponse(
                status_code=500,
                content={"error": str(e), "workflow_id": workflow_id},
            )


@router.post(
    "/pipeline/{workflow_id}/review",
    summary="Submit human review for content",
    operation_id="submitReview",
)
async def submit_review(
    workflow_id: str,
    action: ReviewAction = Query(...),
    comments: str = Query(""),
    reviewer_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    state = await _load_state(workflow_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    state.human_review = HumanReview(
        reviewer_id=reviewer_id or "anonymous",
        action=action,
        comments=comments,
        reviewed_at=datetime.now(UTC).isoformat(),
    )

    if action == ReviewAction.APPROVED:
        state = await pipeline.run_finalizer(state)
    elif action == ReviewAction.CHANGES_REQUESTED:
        logger.info("Review changes requested for %s: %s", workflow_id, comments)
    elif action == ReviewAction.REJECTED:
        state.errors.append(f"Content rejected: {comments}")

    await _save_state(state, db)

    return JSONResponse(content=_state_to_response(state))


@router.get(
    "/pipeline/{workflow_id}",
    summary="Get pipeline workflow status",
    operation_id="getPipelineStatus",
)
async def get_pipeline_status(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    state = await _load_state(workflow_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return JSONResponse(content=_state_to_response(state))


@router.get(
    "/pipeline/{workflow_id}/content",
    summary="Get full content from a pipeline workflow",
    operation_id="getPipelineContent",
)
async def get_pipeline_content(
    workflow_id: str,
    include_draft: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    state = await _load_state(workflow_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return JSONResponse(
        content={
            "workflow_id": workflow_id,
            "topic": state.topic,
            "final_content": state.final_content or state.draft_content,
            "draft_content": state.draft_content if include_draft else None,
            "word_count": len((state.final_content or state.draft_content).split()),
            "metadata": {
                "seo": state.seo_metadata,
                "fact_check": state.fact_check_results,
                "compliance": state.compliance_results,
            },
        }
    )


@router.get(
    "/pipeline/{workflow_id}/events",
    summary="Stream pipeline execution events via SSE",
    operation_id="streamPipelineEvents",
)
async def stream_pipeline_events(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    state = await _load_state(workflow_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    queue = sse_manager.add_connection(workflow_id)

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'connected', 'workflow_id': workflow_id})}\n\n"

            for node_name, result in state.node_results.items():
                event = {
                    "type": "node_completed",
                    "node": node_name,
                    "status": result.status.value,
                    "tokens_used": result.tokens_used,
                    "latency_ms": result.latency_ms,
                    "error": result.error,
                }
                yield f"data: {json.dumps(event)}\n\n"

            if state.all_nodes_completed() or state.has_failures():
                status = "completed" if state.all_nodes_completed() else "failed"
                yield f"data: {json.dumps({'type': 'complete', 'status': status})}\n\n"
                return

            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield message
                    if '"type": "pipeline_completed"' in message or '"type": "pipeline_failed"' in message:
                        break
                except TimeoutError:
                    yield f": heartbeat {int(datetime.now(UTC).timestamp())}\n\n"
        finally:
            sse_manager.remove_connection(workflow_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/pipeline/{workflow_id}/cancel",
    summary="Cancel a running pipeline workflow",
    operation_id="cancelPipeline",
)
async def cancel_pipeline(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    state = await _load_state(workflow_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    state.errors.append("Pipeline cancelled by user")

    await _save_state(state, db)

    if db:
        try:
            uow = UnitOfWork(db)
            await uow.pipelines.update_status(workflow_id, "cancelled")
            await uow.commit()
        except Exception:
            pass

    await sse_manager.broadcast_pipeline_event(
        workflow_id, "pipeline_cancelled", status="cancelled",
    )

    logger.info("Pipeline cancelled: %s", workflow_id)
    return JSONResponse(content={"workflow_id": workflow_id, "status": "cancelled"})


@router.get(
    "/pipeline/{workflow_id}/timeline",
    summary="Get execution timeline for a pipeline",
    operation_id="getPipelineTimeline",
)
async def get_pipeline_timeline(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    state = await _load_state(workflow_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    timeline = []
    for node_name, result in state.node_results.items():
        timeline.append(
            {
                "node": node_name,
                "status": result.status.value,
                "started_at": result.started_at,
                "completed_at": result.completed_at,
                "latency_ms": result.latency_ms,
                "tokens_used": result.tokens_used,
                "error": result.error,
            }
        )

    return JSONResponse(
        content={
            "workflow_id": workflow_id,
            "timeline": timeline,
        }
    )
