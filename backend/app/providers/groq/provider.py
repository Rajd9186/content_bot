from __future__ import annotations

import time
from typing import Optional

from groq import AsyncGroq

from app.providers.base.llm_provider import BaseLLMProvider, LLMResponse


class GroqProvider(BaseLLMProvider):
    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
        api_key: str = "",
        base_url: Optional[str] = None,
    ):
        super().__init__(model, api_key, base_url)
        self.client = AsyncGroq(api_key=api_key)

    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None,
    ) -> LLMResponse:
        start = time.monotonic()
        kwargs = dict(model=self.model, messages=messages, temperature=temperature)
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        if response_format:
            kwargs["response_format"] = response_format

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        usage = response.usage
        duration = (time.monotonic() - start) * 1000

        return LLMResponse(
            content=choice.message.content or "",
            model=self.model,
            provider=self.name(),
            duration_ms=duration,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
        )

    def name(self) -> str:
        return "groq"
