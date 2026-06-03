from __future__ import annotations

import logging

from app.agents.provider.anthropic import AnthropicProvider
from app.agents.provider.base import BaseProvider
from app.agents.provider.groq import GroqProvider
from app.agents.provider.local import LocalProvider
from app.agents.provider.nvidia import NvidiaProvider
from app.agents.provider.ollama import OllamaProvider
from app.agents.provider.openai import OpenAIProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, name: str, provider: BaseProvider) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> BaseProvider | None:
        return self._providers.get(name)

    def get_or_create(self, name: str, model: str | None = None) -> BaseProvider:
        existing = self._providers.get(name)
        if existing:
            return existing
        provider = self._create(name, model)
        self._providers[name] = provider
        return provider

    def _create(self, name: str, model: str | None = None) -> BaseProvider:
        normalized = name.lower().replace("_", "-")
        if normalized in ("openai", "gpt-4o", "gpt-4", "gpt-3.5"):
            return OpenAIProvider(model or "gpt-4o")
        elif normalized in ("anthropic", "claude", "claude-sonnet", "claude-opus"):
            return AnthropicProvider(model or "claude-sonnet-4-20250514")
        elif normalized in ("groq", "llama"):
            return GroqProvider(model or "llama-3.3-70b-versatile")
        elif normalized == "nvidia":
            return NvidiaProvider(model or "meta/llama-3.1-70b-instruct")
        elif normalized in ("ollama", "gpt-oss"):
            default_ollama = "gpt-oss:120b"
            return OllamaProvider(model or default_ollama)
        elif normalized in ("local", "llamacpp"):
            return LocalProvider(model or "local-model")
        else:
            logger.warning("Unknown provider %s, defaulting to OpenAI", name)
            return OpenAIProvider(model or "gpt-4o")

    def all_providers(self) -> dict[str, BaseProvider]:
        return dict(self._providers)


provider_factory = ProviderFactory()
