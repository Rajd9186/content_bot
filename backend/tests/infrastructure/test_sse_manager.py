from __future__ import annotations

import asyncio

import pytest

from app.infrastructure.sse.manager import SSEConnectionManager


@pytest.fixture
def sse() -> SSEConnectionManager:
    return SSEConnectionManager()


class TestSSEConnectionManager:
    async def test_add_connection(self, sse: SSEConnectionManager) -> None:
        q = sse.add_connection("wf-1")
        assert q is not None
        assert "wf-1" in sse._connections

    async def test_remove_connection(self, sse: SSEConnectionManager) -> None:
        q = sse.add_connection("wf-2")
        sse.remove_connection("wf-2", q)
        assert "wf-2" not in sse._connections

    async def test_remove_nonexistent_connection(self, sse: SSEConnectionManager) -> None:
        q = asyncio.Queue()
        sse.remove_connection("nonexistent", q)

    async def test_broadcast_delivers_to_queue(self, sse: SSEConnectionManager) -> None:
        q = sse.add_connection("wf-bcast")
        await sse.broadcast_pipeline_event("wf-bcast", "node_completed", node="research", status="success")
        msg = await asyncio.wait_for(q.get(), timeout=1.0)
        assert "node_completed" in msg
        assert "research" in msg

    async def test_multiple_connections_per_workflow(self, sse: SSEConnectionManager) -> None:
        q1 = sse.add_connection("wf-multi")
        q2 = sse.add_connection("wf-multi")
        assert len(sse._connections["wf-multi"]) == 2

    async def test_broadcast_to_multiple_connections(self, sse: SSEConnectionManager) -> None:
        q1 = sse.add_connection("wf-multi-bcast")
        q2 = sse.add_connection("wf-multi-bcast")
        await sse.broadcast_pipeline_event("wf-multi-bcast", "test", status="ok")
        msg1 = await asyncio.wait_for(q1.get(), timeout=1.0)
        msg2 = await asyncio.wait_for(q2.get(), timeout=1.0)
        assert "test" in msg1
        assert "test" in msg2

    async def test_total_connections_tracking(self, sse: SSEConnectionManager) -> None:
        q1 = sse.add_connection("wf-count-1")
        q2 = sse.add_connection("wf-count-2")
        assert sse.total_connections == 2
        sse.remove_connection("wf-count-1", q1)
        assert sse.total_connections == 1

    async def test_active_workflows_count(self, sse: SSEConnectionManager) -> None:
        sse.add_connection("wf-aw-1")
        sse.add_connection("wf-aw-2")
        assert sse.active_workflows == 2

    async def test_broadcast_to_empty_workflow(self, sse: SSEConnectionManager) -> None:
        await sse.broadcast_pipeline_event("wf-empty", "test", status="ok")

    async def test_remove_last_connection_clears_workflow(self, sse: SSEConnectionManager) -> None:
        q = sse.add_connection("wf-last")
        sse.remove_connection("wf-last", q)
        assert "wf-last" not in sse._connections
