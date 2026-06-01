from __future__ import annotations

import time
from collections import defaultdict
from typing import Any


class MetricsCollector:
    def __init__(self) -> None:
        self._counters: dict[str, float] = defaultdict(float)
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._gauges: dict[str, float] = defaultdict(float)
        self._start_time = time.monotonic()

    def inc_counter(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        key = self._labelled_key(name, labels)
        self._counters[key] += value

    def observe_histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._labelled_key(name, labels)
        self._histograms[key].append(value)

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._labelled_key(name, labels)
        self._gauges[key] = value

    def record_agent_latency(self, agent: str, provider: str, latency_ms: float) -> None:
        labels = {"agent": agent, "provider": provider}
        self.observe_histogram("agent_latency_ms", latency_ms, labels)

    def record_agent_tokens(self, agent: str, provider: str, tokens: int) -> None:
        labels = {"agent": agent, "provider": provider}
        self.inc_counter("agent_tokens_total", float(tokens), labels)

    def record_agent_retry(self, agent: str, provider: str) -> None:
        labels = {"agent": agent, "provider": provider}
        self.inc_counter("agent_retries_total", labels=labels)

    def record_validation_failure(self, agent: str) -> None:
        self.inc_counter("validation_failures_total", labels={"agent": agent})

    def record_compression_ratio(self, agent: str, ratio: float) -> None:
        self.observe_histogram("compression_ratio", ratio, labels={"agent": agent})

    def record_workflow_duration(self, duration_ms: float, status: str) -> None:
        self.observe_histogram("workflow_duration_ms", duration_ms, labels={"status": status})

    def format_prometheus(self) -> str:
        lines: list[str] = []
        lines.append("# HELP app_uptime_seconds Application uptime in seconds")
        lines.append("# TYPE app_uptime_seconds gauge")
        uptime = time.monotonic() - self._start_time
        lines.append(f"app_uptime_seconds {uptime:.1f}")

        for key, value in sorted(self._counters.items()):
            name, labels = self._parse_key(key)
            lines.append(f"# HELP {name} total")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name}{labels} {value:.0f}")

        for key, values in sorted(self._histograms.items()):
            name, labels = self._parse_key(key)
            if not values:
                continue
            lines.append(f"# HELP {name} observations")
            lines.append(f"# TYPE {name} summary")
            sorted_vals = sorted(values)
            count = len(sorted_vals)
            total = sum(sorted_vals)
            lines.append(f"{name}_count{labels} {count}")
            lines.append(f"{name}_sum{labels} {total:.2f}")
            for quantile in (0.5, 0.9, 0.95, 0.99):
                idx = min(int(count * quantile), count - 1)
                safe_labels = labels.replace("}", f',quantile="{quantile}"}}') if labels else f'{{quantile="{quantile}"}}'
                lines.append(f"{name}{safe_labels} {sorted_vals[idx]:.2f}")

        for key, value in sorted(self._gauges.items()):
            name, labels = self._parse_key(key)
            lines.append(f"# HELP {name} current value")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name}{labels} {value:.2f}")

        return "\n".join(lines) + "\n"

    def _labelled_key(self, name: str, labels: dict[str, str] | None = None) -> str:
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _parse_key(self, key: str) -> tuple[str, str]:
        if "{" in key:
            name = key[: key.index("{")]
            labels = key[key.index("{") :]
            return name, labels
        return key, "{}"

    def get_stats(self) -> dict[str, Any]:
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histogram_counts": {k: len(v) for k, v in self._histograms.items()},
        }


metrics_collector = MetricsCollector()
