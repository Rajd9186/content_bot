from __future__ import annotations

from app.infrastructure.metrics.collector import MetricsCollector


class TestMetricsCollector:
    def test_counter_increment(self) -> None:
        mc = MetricsCollector()
        mc.inc_counter("test_counter")
        assert mc._counters["test_counter"] == 1.0

    def test_counter_increment_by_value(self) -> None:
        mc = MetricsCollector()
        mc.inc_counter("test_counter", value=5.0)
        assert mc._counters["test_counter"] == 5.0

    def test_counter_with_labels(self) -> None:
        mc = MetricsCollector()
        mc.inc_counter("test_counter", labels={"agent": "research"})
        assert 'test_counter{agent="research"}' in mc._counters

    def test_histogram_observe(self) -> None:
        mc = MetricsCollector()
        mc.observe_histogram("test_hist", 100.0)
        mc.observe_histogram("test_hist", 200.0)
        assert len(mc._histograms["test_hist"]) == 2

    def test_gauge_set(self) -> None:
        mc = MetricsCollector()
        mc.set_gauge("test_gauge", 42.0)
        assert mc._gauges["test_gauge"] == 42.0

    def test_record_agent_latency(self) -> None:
        mc = MetricsCollector()
        mc.record_agent_latency("research", "groq", 1500.0)
        key = 'agent_latency_ms{agent="research",provider="groq"}'
        assert key in mc._histograms
        assert 1500.0 in mc._histograms[key]

    def test_record_agent_tokens(self) -> None:
        mc = MetricsCollector()
        mc.record_agent_tokens("writer", "groq", 2000)
        key = 'agent_tokens_total{agent="writer",provider="groq"}'
        assert mc._counters[key] == 2000.0

    def test_record_validation_failure(self) -> None:
        mc = MetricsCollector()
        mc.record_validation_failure("planner")
        key = 'validation_failures_total{agent="planner"}'
        assert mc._counters[key] == 1.0

    def test_record_workflow_duration(self) -> None:
        mc = MetricsCollector()
        mc.record_workflow_duration(300000.0, "completed")
        key = 'workflow_duration_ms{status="completed"}'
        assert key in mc._histograms

    def test_record_compression_ratio(self) -> None:
        mc = MetricsCollector()
        mc.record_compression_ratio("research", 0.5)
        key = 'compression_ratio{agent="research"}'
        assert key in mc._histograms
        assert 0.5 in mc._histograms[key]

    def test_format_prometheus_includes_uptime(self) -> None:
        mc = MetricsCollector()
        output = mc.format_prometheus()
        assert "app_uptime_seconds" in output

    def test_format_prometheus_includes_counter(self) -> None:
        mc = MetricsCollector()
        mc.inc_counter("test_total", value=10.0)
        output = mc.format_prometheus()
        assert "test_total" in output
        assert "10" in output

    def test_format_prometheus_includes_gauge(self) -> None:
        mc = MetricsCollector()
        mc.set_gauge("active_connections", 5.0)
        output = mc.format_prometheus()
        assert "active_connections" in output

    def test_format_prometheus_includes_histogram(self) -> None:
        mc = MetricsCollector()
        mc.observe_histogram("latency_ms", 100.0)
        mc.observe_histogram("latency_ms", 200.0)
        output = mc.format_prometheus()
        assert "latency_ms_count" in output
        assert "latency_ms_sum" in output

    def test_get_stats(self) -> None:
        mc = MetricsCollector()
        mc.inc_counter("c1", value=5.0)
        mc.set_gauge("g1", 10.0)
        mc.observe_histogram("h1", 100.0)
        stats = mc.get_stats()
        assert "counters" in stats
        assert "gauges" in stats
        assert "histogram_counts" in stats
        assert stats["histogram_counts"]["h1"] == 1

    def test_labelled_key_no_labels(self) -> None:
        mc = MetricsCollector()
        key = mc._labelled_key("test", None)
        assert key == "test"

    def test_labelled_key_with_labels(self) -> None:
        mc = MetricsCollector()
        key = mc._labelled_key("test", {"agent": "research", "provider": "groq"})
        assert key == 'test{agent="research",provider="groq"}'

    def test_parse_key_no_labels(self) -> None:
        mc = MetricsCollector()
        name, labels = mc._parse_key("test")
        assert name == "test"
        assert labels == "{}"

    def test_parse_key_with_labels(self) -> None:
        mc = MetricsCollector()
        name, labels = mc._parse_key('test{agent="research"}')
        assert name == "test"
        assert labels == '{agent="research"}'
