from __future__ import annotations

import logging
import os
import time
from typing import Any

from app.agents.contracts import TokenUsage
from app.agents.provider.base import BaseProvider, ProviderRequest, ProviderResponse

logger = logging.getLogger(__name__)


class NvidiaProvider(BaseProvider):
    def __init__(self, model: str = "nvidia/nemotron-3-super-120b-a12b") -> None:
        super().__init__("nvidia")
        self._model = model
        self._api_key = os.getenv("NVIDIA_API_KEY", "")

    @property
    def _base_url(self) -> str:
        return "https://integrate.api.nvidia.com/v1"

    async def execute(self, request: ProviderRequest) -> ProviderResponse:
        import aiohttp

        start = time.monotonic()
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": request.model or self._model,
            "messages": [],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.system_prompt:
            body["messages"].append({"role": "system", "content": request.system_prompt})
        body["messages"].extend(request.messages)
        if request.stop_sequences:
            body["stop"] = request.stop_sequences

        try:
            timeout = aiohttp.ClientTimeout(total=request.timeout_ms / 1000)
            async with aiohttp.ClientSession(timeout=timeout) as session, \
                    session.post(url, json=body, headers=headers) as resp:
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

                    choice = raw["choices"][0]
                    content = choice.get("message", {}).get("content", "")
                    usage = raw.get("usage", {})
                    tokens = TokenUsage(
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=usage.get("completion_tokens", 0),
                        total_tokens=usage.get("total_tokens", 0),
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
