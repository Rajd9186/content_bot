from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

from app.agents.prompt.templates import get_system_prompt, get_user_prompt

logger = logging.getLogger(__name__)


class PromptContext:
    def __init__(
        self,
        agent_type: str,
        template_version: str = "1.0",
        correlation_id: str | None = None,
    ) -> None:
        self.agent_type = agent_type
        self.template_version = template_version
        self.correlation_id = correlation_id
        self.system_prompt: str = ""
        self.user_prompt: str = ""
        self.messages: list[dict[str, str]] = []
        self.metadata: dict[str, Any] = {}
        self._created_at = time.time()

    @property
    def prompt_hash(self) -> str:
        raw = f"{self.system_prompt}|{self.user_prompt}|{self.template_version}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_type": self.agent_type,
            "template_version": self.template_version,
            "correlation_id": self.correlation_id,
            "prompt_hash": self.prompt_hash,
            "system_prompt_length": len(self.system_prompt),
            "user_prompt_length": len(self.user_prompt),
            "message_count": len(self.messages),
            "metadata": self.metadata,
        }


class PromptEngine:
    def __init__(self) -> None:
        self._version = "2.0"

    async def build(
        self,
        agent_type: str,
        correlation_id: str | None = None,
        template_kwargs: dict[str, Any] | None = None,
        context: PromptContext | None = None,
    ) -> PromptContext:
        ctx = context or PromptContext(
            agent_type=agent_type,
            template_version=self._version,
            correlation_id=correlation_id,
        )

        ctx.system_prompt = get_system_prompt(agent_type)
        raw_kwargs = template_kwargs or {}
        ctx.user_prompt = get_user_prompt(agent_type, **raw_kwargs)
        ctx.metadata["template_kwargs_keys"] = list(raw_kwargs.keys())

        ctx.messages = []
        if ctx.system_prompt:
            ctx.messages.append({"role": "system", "content": ctx.system_prompt})
        ctx.messages.append({"role": "user", "content": ctx.user_prompt})

        return ctx

    def build_sync(
        self,
        agent_type: str,
        correlation_id: str | None = None,
        template_kwargs: dict[str, Any] | None = None,
        context: PromptContext | None = None,
    ) -> PromptContext:
        ctx = context or PromptContext(
            agent_type=agent_type,
            template_version=self._version,
            correlation_id=correlation_id,
        )

        ctx.system_prompt = get_system_prompt(agent_type)
        raw_kwargs = template_kwargs or {}
        ctx.user_prompt = get_user_prompt(agent_type, **raw_kwargs)
        ctx.metadata["template_kwargs_keys"] = list(raw_kwargs.keys())

        ctx.messages = []
        if ctx.system_prompt:
            ctx.messages.append({"role": "system", "content": ctx.system_prompt})
        ctx.messages.append({"role": "user", "content": ctx.user_prompt})

        return ctx

    async def build_conversation(
        self,
        agent_type: str,
        messages: list[dict[str, str]],
        correlation_id: str | None = None,
    ) -> PromptContext:
        ctx = PromptContext(
            agent_type=agent_type,
            template_version=self._version,
            correlation_id=correlation_id,
        )
        ctx.system_prompt = get_system_prompt(agent_type)
        ctx.user_prompt = messages[-1]["content"] if messages else ""
        ctx.messages = []
        if ctx.system_prompt:
            ctx.messages.append({"role": "system", "content": ctx.system_prompt})
        ctx.messages.extend(messages)
        return ctx


prompt_engine = PromptEngine()
