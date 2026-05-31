from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.infrastructure.metrics.collector import metrics_collector


class RetrievalMetricsService:
    def __init__(self) -> None:
        self._retrieval_count: dict[str, int] = defaultdict(int)
        self._retrieval_latency: dict[str, list[float]] = defaultdict(list)
        self._relevance_scores: dict[str, list[float]] = defaultdict(list)
        self._usage_frequency: dict[str, int] = defaultdict(int)

    def record_retrieval(
        self,
        project_id: str,
        query: str,
        latency_ms: float,
        results_count: int,
        relevance_scores: list[float] | None = None,
    ) -> None:
        self._retrieval_count[project_id] += 1
        self._retrieval_latency[project_id].append(latency_ms)
        metrics_collector.observe_histogram(
            "memory_retrieval_latency_ms", latency_ms,
            labels={"project_id": project_id[:8]},
        )
        metrics_collector.inc_counter(
            "memory_retrieval_total",
            labels={"project_id": project_id[:8]},
        )
        if relevance_scores:
            avg_score = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
            self._relevance_scores[project_id].append(avg_score)
            metrics_collector.observe_histogram(
                "memory_relevance_score", avg_score,
                labels={"project_id": project_id[:8]},
            )

    def record_memory_usage(self, memory_id: str) -> None:
        self._usage_frequency[memory_id] += 1
        metrics_collector.inc_counter(
            "memory_usage_total",
            labels={"memory_id": memory_id[:8]},
        )

    def get_stats(self, project_id: str | None = None) -> dict[str, Any]:
        if project_id:
            latencies = self._retrieval_latency.get(project_id, [])
            scores = self._relevance_scores.get(project_id, [])
            return {
                "project_id": project_id,
                "total_retrievals": self._retrieval_count.get(project_id, 0),
                "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
                "avg_relevance_score": sum(scores) / len(scores) if scores else 0,
                "last_retrieval_count": len(latencies),
            }
        return {
            "total_retrievals": dict(self._retrieval_count),
            "total_memories_tracked": len(self._usage_frequency),
        }


retrieval_metrics = RetrievalMetricsService()
