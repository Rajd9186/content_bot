from __future__ import annotations

import logging
from typing import Optional

from app.research.providers.base import BaseSearchProvider

logger = logging.getLogger(__name__)


class SearchProviderFactory:
    def __init__(self) -> None:
        self._providers: dict[str, BaseSearchProvider] = {}

    def register(self, provider: BaseSearchProvider) -> None:
        self._providers[provider.name] = provider
        logger.info("Registered search provider: %s", provider.name)

    def get(self, name: str) -> Optional[BaseSearchProvider]:
        return self._providers.get(name)

    def get_or_create(self, name: str) -> BaseSearchProvider:
        existing = self.get(name)
        if existing:
            return existing
        
        provider = self._create(name)
        if provider:
            self.register(provider)
        return provider

    def _create(self, name: str) -> Optional[BaseSearchProvider]:
        normalized = name.lower().replace("_", "-")
        
        if normalized == "tavily":
            from app.research.providers.tavily import TavilyProvider
            return TavilyProvider()
        elif normalized == "serper":
            from app.research.providers.serper import SerperProvider
            return SerperProvider()
        elif normalized == "mock":
            from app.research.providers.mock import MockSearchProvider
            return MockSearchProvider()
        
        logger.warning("Unknown search provider: %s", name)
        return None

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())


search_provider_factory = SearchProviderFactory()