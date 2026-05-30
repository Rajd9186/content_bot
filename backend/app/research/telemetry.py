from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ResearchMetrics:
    query_count: int = 0
    total_sources_ingested: int = 0
    total_duplicates_removed: int = 0
    total_spam_filtered: int = 0
    avg_sources_per_query: float = 0.0
    avg_synthesis_latency_ms: float = 0.0
    total_embeddings_generated: int = 0
    total_vector_searches: int = 0
    citation_validation_errors: int = 0
    hallucinated_citations_detected: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_count": self.query_count,
            "total_sources_ingested": self.total_sources_ingested,
            "total_duplicates_removed": self.total_duplicates_removed,
            "total_spam_filtered": self.total_spam_filtered,
            "avg_sources_per_query": self.avg_sources_per_query,
            "avg_synthesis_latency_ms": self.avg_synthesis_latency_ms,
            "total_embeddings_generated": self.total_embeddings_generated,
            "total_vector_searches": self.total_vector_searches,
            "citation_validation_errors": self.citation_validation_errors,
            "hallucinated_citations_detected": self.hallucinated_citations_detected,
        }


class ResearchTelemetry:
    def __init__(self) -> None:
        self._metrics = ResearchMetrics()
        self._query_latencies: list[float] = []
        self._synthesis_latencies: list[float] = []

    def record_query(self, source_count: int, latency_ms: float) -> None:
        self._metrics.query_count += 1
        self._metrics.total_sources_ingested += source_count
        self._query_latencies.append(latency_ms)
        self._update_averages()

    def record_deduplication(self, duplicates: int, spam: int) -> None:
        self._metrics.total_duplicates_removed += duplicates
        self._metrics.total_spam_filtered += spam

    def record_synthesis(self, latency_ms: float) -> None:
        self._synthesis_latencies.append(latency_ms)
        self._metrics.avg_synthesis_latency_ms = (
            sum(self._synthesis_latencies) / len(self._synthesis_latencies)
        )

    def record_embedding_generation(self, count: int) -> None:
        self._metrics.total_embeddings_generated += count

    def record_vector_search(self) -> None:
        self._metrics.total_vector_searches += 1

    def record_citation_error(self, hallucinated: bool = False) -> None:
        self._metrics.citation_validation_errors += 1
        if hallucinated:
            self._metrics.hallucinated_citations_detected += 1

    def _update_averages(self) -> None:
        if self._metrics.query_count > 0:
            self._metrics.avg_sources_per_query = (
                self._metrics.total_sources_ingested / self._metrics.query_count
            )

    def get_metrics(self) -> ResearchMetrics:
        return self._metrics

    def get_summary(self) -> dict[str, Any]:
        return {
            **self._metrics.to_dict(),
            "uptime_seconds": (
                datetime.now(timezone.utc) - datetime.now(timezone.utc)
            ).total_seconds(),
        }


research_telemetry = ResearchTelemetry()