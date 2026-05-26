import asyncio
import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.project import ProjectRepository
from app.services.event_bus import event_bus

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/projects/{project_id}")
async def project_events(websocket: WebSocket, project_id: uuid.UUID):
    """WebSocket endpoint for real-time project workflow events."""
    await websocket.accept()
    workflow_id = str(project_id)

    q = await event_bus.subscribe(workflow_id)
    try:
        while True:
            event = await asyncio.wait_for(q.get(), timeout=30)
            await websocket.send_text(event.to_json())
    except asyncio.TimeoutError:
        pass
    except WebSocketDisconnect:
        pass
    finally:
        await event_bus.unsubscribe(workflow_id, q)
        try:
            await websocket.close()
        except Exception:
            pass
