from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Optional

from app.agents.contracts import TokenUsage
from app.agents.provider.base import BaseProvider, ProviderRequest, ProviderResponse

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    def __init__(self, model: str = "llama3.2") -> None:
        super().__init__("ollama")
        self._model = model
        self._api_key = os.getenv("OLLAMA_API_KEY", "")
        self._host = os.getenv(
            "OLLAMA_HOST",
            "https://ollama.com" if self._api_key else "http://localhost:11434",
        )

    async def execute(self, request: ProviderRequest) -> ProviderResponse:
        import ollama

        start = time.monotonic()
        client_kwargs: dict[str, Any] = {"host": self._host}
        if self._api_key:
            client_kwargs["headers"] = {
                "Authorization": f"Bearer {self._api_key}"
            }

        client = ollama.Client(**client_kwargs)
        model = request.model or self._model

        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.extend(request.messages)

        try:
            def _call() -> Any:
                return client.chat(
                    model=model,
                    messages=messages,
                    stream=False,
                    options={
                        "temperature": request.temperature,
                        "num_predict": request.max_tokens,
                    },
                )

            raw = await asyncio.get_event_loop().run_in_executor(None, _call)
            elapsed = (time.monotonic() - start) * 1000

            content = raw.get("message", {}).get("content", "")
            usage_info = raw.get("usage", {}) or {}
            tokens = TokenUsage(
                prompt_tokens=usage_info.get("prompt_tokens", 0),
                completion_tokens=usage_info.get("completion_tokens", 0),
                total_tokens=usage_info.get("total_tokens", 0),
                provider=self._name,
                model=model,
            )
            return ProviderResponse(
                content=content, token_usage=tokens,
                latency_ms=elapsed, success=True,
                provider=self._name, model=model,
                raw_response=raw,
            )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            logger.exception("Ollama request failed: %s", e)
            return ProviderResponse(
                success=False, error=str(e),
                latency_ms=elapsed, provider=self._name,
                model=model,
            )
