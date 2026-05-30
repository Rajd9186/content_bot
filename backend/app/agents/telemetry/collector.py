from __future__ import annotations

import logging
from typing import Any

from app.agents.contracts import AgentTelemetry, TokenUsage

logger = logging.getLogger(__name__)


class TelemetryCollector:
    def __init__(self) -> None:
        self._records: list[AgentTelemetry] = []
        self._hooks: list[Any] = []

    def record(self, telemetry: AgentTelemetry) -> None:
        self._records.append(telemetry)
        self._emit(telemetry)

    def add_hook(self, hook: Any) -> None:
        self._hooks.append(hook)

    def get_records(
        self, correlation_id: str | None = None,
    ) -> list[AgentTelemetry]:
        if correlation_id:
            return [
                r for r in self._records
                if r.correlation_id == correlation_id
            ]
        return list(self._records)

    def get_latest(self, agent_name: str) -> AgentTelemetry | None:
        for record in reversed(self._records):
            if record.agent_name == agent_name:
                return record
        return None

    def create_telemetry(
        self,
        agent_name: str,
        correlation_id: str | None = None,
        workflow_id: str | None = None,
    ) -> AgentTelemetry:
        return AgentTelemetry(
            agent_name=agent_name,
            status="PENDING",
            correlation_id=correlation_id,
            workflow_id=workflow_id,
        )

    def update_token_usage(
        self, telemetry: AgentTelemetry, usage: TokenUsage,
    ) -> None:
        telemetry.token_usage = usage

    def _emit(self, telemetry: AgentTelemetry) -> None:
        for hook in self._hooks:
            try:
                hook(telemetry)
            except Exception as e:
                logger.error("Telemetry hook failed: %s", e)

    def summary(
        self, correlation_id: str | None = None,
    ) -> dict[str, Any]:
        records = self.get_records(correlation_id)
        if not records:
            return {"total_agents": 0}

        total_tokens = sum(
            r.token_usage.total_tokens for r in records
        )
        total_latency = sum(r.latency_ms for r in records)
        retries = sum(r.retry_count for r in records)
        fallbacks = sum(1 for r in records if r.fallback_used)
        errors = [r.error for r in records if r.error]

        return {
            "total_agents": len(records),
            "total_tokens": total_tokens,
            "total_latency_ms": total_latency,
            "total_retries": retries,
            "total_fallbacks": fallbacks,
            "errors": errors,
            "agents": [
                {
                    "name": r.agent_name,
                    "status": r.status,
                    "latency_ms": r.latency_ms,
                    "tokens": r.token_usage.total_tokens,
                    "retries": r.retry_count,
                    "fallback": r.fallback_used,
                    "error": r.error,
                }
                for r in records
            ],
        }


telemetry_collector = TelemetryCollector()
