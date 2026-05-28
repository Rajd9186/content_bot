from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from app.agents.contracts import TokenUsage


@dataclass
class ProviderRequest:
    model: str
    system_prompt: Optional[str] = None
    messages: list[dict[str, str]] = field(default_factory=list)
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout_ms: int = 60000
    stop_sequences: Optional[list[str]] = None


@dataclass
class ProviderResponse:
    content: str = ""
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    latency_ms: float = 0.0
    success: bool = False
    error: Optional[str] = None
    provider: str = ""
    model: str = ""
    raw_response: Optional[Any] = None


class BaseProvider(ABC):
    def __init__(self, name: str) -> None:
        self._name = name
        self._model: str = ""

    @property
    def name(self) -> str:
        return self._name

    @property
    def model(self) -> str:
        return self._model

    @abstractmethod
    async def execute(self, request: ProviderRequest) -> ProviderResponse:
        pass

    async def execute_with_retry(
        self, request: ProviderRequest, max_retries: int = 3,
    ) -> ProviderResponse:
        last_error: Optional[str] = None
        for attempt in range(max_retries + 1):
            resp = await self.execute(request)
            if resp.success:
                return resp
            last_error = resp.error
            if attempt < max_retries:
                delay = min(2.0 ** attempt * 1.0, 30.0)
                await self._sleep(delay)
        return ProviderResponse(
            success=False,
            error=f"All {max_retries + 1} retries failed: {last_error}",
            provider=self._name,
            model=self._model,
        )

    async def _sleep(self, seconds: float) -> None:
        import asyncio
        await asyncio.sleep(seconds)
