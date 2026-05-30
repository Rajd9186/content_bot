from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from app.research.models import ResearchQuery

logger = logging.getLogger(__name__)


class BaseSearchProvider(ABC):
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    async def search(
        self,
        query: str,
        research_query: ResearchQuery,
    ) -> list[dict[str, Any]]:
        pass

    async def search_with_retry(
        self,
        query: str,
        research_query: ResearchQuery,
        max_retries: int = 2,
    ) -> list[dict[str, Any]]:
        last_error: Optional[str] = None
        
        for attempt in range(max_retries + 1):
            try:
                results = await self.search(query, research_query)
                if results:
                    return results
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "Search attempt %d failed for %s: %s",
                    attempt + 1, query, e
                )
            
            if attempt < max_retries:
                import asyncio
                await asyncio.sleep(1.0 * (attempt + 1))
        
        logger.warning(
            "All %d search attempts failed for: %s",
            max_retries + 1, query
        )
        return []