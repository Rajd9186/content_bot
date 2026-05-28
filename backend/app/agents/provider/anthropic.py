from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Optional

from app.agents.contracts import TokenUsage
from app.agents.provider.base import BaseProvider, ProviderRequest, ProviderResponse

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    def __init__(self, model: str = "claude-sonnet-4-20250514") -> None:
        super().__init__("anthropic")
        self._model = model
        self._api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self._api_version = "2023-06-01"

    @property
    def _base_url(self) -> str:
        return "https://api.anthropic.com/v1"

    async def execute(self, request: ProviderRequest) -> ProviderResponse:
        import aiohttp

        start = time.monotonic()
        url = f"{self._base_url}/messages"
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": self._api_version,
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": request.model or self._model,
            "max_tokens": request.max_tokens,
            "messages": request.messages,
        }
        if request.system_prompt:
            body["system"] = request.system_prompt
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.stop_sequences:
            body["stop_sequences"] = request.stop_sequences

        try:
            timeout = aiohttp.ClientTimeout(total=request.timeout_ms / 1000)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=body, headers=headers) as resp:
                    elapsed = (time.monotonic() - start) * 1000
                    raw = await resp.json()

                    if resp.status != 200:
                        error_msg = raw.get("error", {}).get("message", str(raw))
                        return ProviderResponse(
                            success=False, error=error_msg,
                            latency_ms=elapsed, provider=self._name,
                            model=request.model or self._model,
                            raw_response=raw,
                        )

                    content = ""
                    for block in raw.get("content", []):
                        if block.get("type") == "text":
                            content += block.get("text", "")

                    usage = raw.get("usage", {})
                    tokens = TokenUsage(
                        prompt_tokens=usage.get("input_tokens", 0),
                        completion_tokens=usage.get("output_tokens", 0),
                        total_tokens=(
                            usage.get("input_tokens", 0)
                            + usage.get("output_tokens", 0)
                        ),
                        provider=self._name,
                        model=request.model or self._model,
                    )
                    return ProviderResponse(
                        content=content, token_usage=tokens,
                        latency_ms=elapsed, success=True,
                        provider=self._name,
                        model=request.model or self._model,
                        raw_response=raw,
                    )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            return ProviderResponse(
                success=False, error=str(e),
                latency_ms=elapsed, provider=self._name,
                model=request.model or self._model,
            )
