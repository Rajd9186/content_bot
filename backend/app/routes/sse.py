"""Server-Sent Events endpoint for real-time workflow streaming."""

import asyncio
import uuid
import json
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_session
from app.models.workflow import WorkflowExecution
from app.services.event_bus import event_bus
from app.log_config.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/workflows", tags=["Workflow SSE"])

SSE_KEEPALIVE_INTERVAL = settings.sse_keepalive_interval
SSE_RECENT_EVENT_LIMIT = settings.sse_recent_event_limit
SSE_MAX_CONNECTION_TIME = 1800.0  # 30 minutes max subscription


async def _sse_generator(workflow_id: str, after_event_id: str | None = None):
    """Async generator that yields SSE-formatted workflow events.

    1. If after_event_id is provided, replays recent events from DB.
    2. Subscribes to live event stream.
    3. Sends keepalive pings every 15s.
    4. Terminates after SSE_MAX_CONNECTION_TIME seconds.
    """
    q = await event_bus.subscribe(workflow_id)

    try:
        # Step 1: Replay recent events for reconnect recovery
        if after_event_id:
            recent = await event_bus.get_recent_events(
                workflow_id, after_event_id=after_event_id, limit=SSE_RECENT_EVENT_LIMIT,
            )
            for evt in recent:
                yield f"data: {json.dumps(evt, default=str)}\n\n"
        else:
            recent = await event_bus.get_recent_events(workflow_id, limit=20)
            for evt in recent:
                yield f"data: {json.dumps(evt, default=str)}\n\n"

        # Step 2: Stream live events with connection timeout
        start_time = asyncio.get_event_loop().time()
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= SSE_MAX_CONNECTION_TIME:
                logger.info("SSE connection max lifetime reached, closing")
                break

            try:
                event = await asyncio.wait_for(q.get(), timeout=SSE_KEEPALIVE_INTERVAL)
                payload = event.to_sse_dict()
                yield f"id: {payload['id']}\ndata: {json.dumps(payload, default=str)}\n\n"
            except asyncio.TimeoutError:
                # Keepalive ping
                yield f": keepalive\n\n"

    except asyncio.CancelledError:
        pass
    finally:
        await event_bus.unsubscribe(workflow_id, q)


@router.get("/{workflow_id}/stream")
async def workflow_sse_stream(
    workflow_id: uuid.UUID = Path(..., description="Workflow execution ID"),
    after_event_id: str = Query(None, description="Reconnect: replay events after this ID"),
    session: AsyncSession = Depends(get_session),
):
    """SSE endpoint that streams real-time workflow agent events.

    On connect (without after_event_id), sends the 20 most recent events.
    On reconnect (with after_event_id), sends all events after that ID.
    Then streams live events as agents execute.

    Event payload:
    ```json
    {
      "id": "uuid",
      "workflow_id": "uuid",
      "type": "agent_started|agent_progress|agent_completed|...",
      "agent": "planner|writer|critique|...",
      "status": "running|completed|failed",
      "message": "Human-readable status",
      "progress": 42.0,
      "payload": {},
      "timestamp": "2026-05-26T16:00:00"
    }
    ```
    """
    # Validate workflow exists
    result = await session.execute(select(WorkflowExecution).where(WorkflowExecution.id == workflow_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return StreamingResponse(
        _sse_generator(str(workflow_id), after_event_id=after_event_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
