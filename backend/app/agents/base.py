from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any, Optional

from pydantic import BaseModel

from app.providers import get_llm_client
from app.providers.base.llm_provider import BaseLLMProvider, LLMResponse
from app.log_config.logger import get_logger
from app.orchestration.retry_engine.retry_middleware import RetryConfig, async_retry

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class AgentMetrics(BaseModel):
    agent_name: str = ""
    duration_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    retry_count: int = 0
    validation_score: float = 0.0
    error: Optional[str] = None


class BaseAgent(ABC, Generic[InputT, OutputT]):
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self._llm: BaseLLMProvider = get_llm_client()
        self._metrics = AgentMetrics(agent_name=self.__class__.__name__)

    @abstractmethod
    def system_prompt(self) -> str:
        ...

    def user_prompt(self, input_data: InputT) -> str:
        return input_data.model_dump_json(indent=2)

    @abstractmethod
    def parse_response(self, response: str, input_data: InputT) -> OutputT:
        ...

    @abstractmethod
    async def run(self, input_data: InputT) -> OutputT:
        ...

    async def call_llm(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None,
    ) -> LLMResponse:
        self.logger.info(
            "LLM call",
            extra={
                "model": self._llm.model,
                "provider": self._llm.name(),
                "messages_count": len(messages),
                "temperature": temperature,
            },
        )
        response = await self._llm.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )
        self._metrics.prompt_tokens += response.prompt_tokens
        self._metrics.completion_tokens += response.completion_tokens
        self._metrics.total_tokens += response.total_tokens
        self._metrics.duration_ms += response.duration_ms
        return response

    def get_metrics(self) -> AgentMetrics:
        return self._metrics

    def reset_metrics(self) -> None:
        self._metrics = AgentMetrics(agent_name=self.__class__.__name__)
