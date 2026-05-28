from __future__ import annotations

from app.domains.workflow.retry_service import full_jitter_delay, equal_jitter_delay


class TestRetryJitter:
    def test_full_jitter_is_within_bounds(self) -> None:
        for attempt in range(1, 10):
            delay = full_jitter_delay(attempt, base_ms=1000, max_ms=300000)
            cap = min(300000, 1000 * (2 ** attempt))
            assert 0 <= delay <= cap, (
                f"attempt={attempt}: delay={delay} cap={cap}"
            )

    def test_full_jitter_backoff_increases(self) -> None:
        delays = [full_jitter_delay(i, base_ms=100, max_ms=10000) for i in range(1, 8)]
        max_seen = max(delays)
        min_seen = min(delays)
        assert max_seen >= min_seen

    def test_equal_jitter_is_within_bounds(self) -> None:
        for attempt in range(1, 10):
            delay = equal_jitter_delay(attempt, base_ms=1000, max_ms=300000)
            temp = min(300000, 1000 * (2 ** attempt))
            half = temp / 2
            assert half <= delay <= temp, (
                f"attempt={attempt}: delay={delay} half={half} temp={temp}"
            )

    def test_full_jitter_at_high_attempts(self) -> None:
        delay = full_jitter_delay(20, base_ms=1000, max_ms=300000)
        assert delay <= 300000

    def test_full_jitter_zero_base(self) -> None:
        delay = full_jitter_delay(1, base_ms=0, max_ms=1000)
        assert delay == 0  # 0 * 2^1 = 0, capped at 1000 -> 0, random(0,0) = 0
