import asyncio
import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import async_session_factory
from app.models.workflow import WorkflowExecution
from app.services.event_bus import event_bus

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/workflows/{workflow_id}")
async def workflow_events_ws(websocket: WebSocket, workflow_id: uuid.UUID):
    """WebSocket endpoint for real-time workflow events.

    Unlike the SSE endpoint, this provides a bi-directional connection
    for clients that prefer WebSockets.
    """
    wid = str(workflow_id)

    # Validate workflow exists
    async with async_session_factory() as session:
        result = await session.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == workflow_id)
        )
        if not result.scalar_one_or_none():
            await websocket.close(code=4004, reason="Workflow not found")
            return

    await websocket.accept()
    q = await event_bus.subscribe(wid)

    try:
        while True:
            event = await asyncio.wait_for(q.get(), timeout=30)
            await websocket.send_text(json.dumps(event.to_sse_dict(), default=str))
    except asyncio.TimeoutError:
        pass
    except WebSocketDisconnect:
        pass
    finally:
        await event_bus.unsubscribe(wid, q)
        try:
            await websocket.close()
        except Exception:
            pass
