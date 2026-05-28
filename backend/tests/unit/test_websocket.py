from __future__ import annotations

from app.websocket.manager import ConnectionManager, WSMessage


class TestConnectionManager:
    async def test_singleton(self) -> None:
        from app.websocket.manager import connection_manager
        assert connection_manager is not None
        assert isinstance(connection_manager, ConnectionManager)

    def test_active_connections_starts_zero(self) -> None:
        mgr = ConnectionManager()
        assert mgr.active_connections == 0

    def test_ws_message_serialization(self) -> None:
        msg = WSMessage(
            type="test.event",
            data={"key": "value"},
            correlation_id="corr-123",
        )
        dumped = msg.model_dump()
        assert dumped["type"] == "test.event"
        assert dumped["data"]["key"] == "value"
        assert dumped["correlation_id"] == "corr-123"
        assert "timestamp" in dumped

    def test_ws_message_defaults(self) -> None:
        msg = WSMessage(type="test.event")
        assert msg.data == {}
        assert msg.timestamp != ""
