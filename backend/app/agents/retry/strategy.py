from __future__ import annotations

import random
from abc import ABC, abstractmethod


class BackoffStrategy(ABC):
    @abstractmethod
    def delay(self, attempt: int) -> float:
        pass


class ExponentialBackoff(BackoffStrategy):
    def __init__(
        self, base_delay_ms: float = 1000.0, max_delay_ms: float = 30000.0,
    ) -> None:
        self._base = base_delay_ms
        self._max = max_delay_ms

    def delay(self, attempt: int) -> float:
        return min(self._base * (2.0 ** (attempt - 1)), self._max)


class FullJitterBackoff(BackoffStrategy):
    def __init__(
        self,
        base_delay_ms: float = 1000.0,
        max_delay_ms: float = 30000.0,
        jitter_factor: float = 0.1,
    ) -> None:
        self._base = base_delay_ms
        self._max = max_delay_ms
        self._jitter_factor = jitter_factor

    def delay(self, attempt: int) -> float:
        exponential = min(self._base * (2.0 ** (attempt - 1)), self._max)
        jitter = random.uniform(0, exponential * self._jitter_factor)
        return min(exponential + jitter, self._max)


class EqualJitterBackoff(BackoffStrategy):
    def __init__(
        self, base_delay_ms: float = 1000.0, max_delay_ms: float = 30000.0,
    ) -> None:
        self._base = base_delay_ms
        self._max = max_delay_ms

    def delay(self, attempt: int) -> float:
        exponential = min(self._base * (2.0 ** (attempt - 1)), self._max)
        half = exponential / 2.0
        jitter = random.uniform(0, half)
        return min(half + jitter, self._max)
