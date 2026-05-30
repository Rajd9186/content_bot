from __future__ import annotations

import logging
import os
from typing import Any

import aiohttp

from app.research.models import ResearchQuery
from app.research.providers.base import BaseSearchProvider

logger = logging.getLogger(__name__)


class SerperProvider(BaseSearchProvider):
    def __init__(self) -> None:
        super().__init__("serper")
        self._api_key = os.getenv("SERPER_API_KEY", "")
        self._base_url = "https://google.serper.dev/search"

    async def search(
        self,
        query: str,
        research_query: ResearchQuery,
    ) -> list[dict[str, Any]]:
        if not self._api_key:
            logger.warning("Serper API key not configured")
            return []

        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self._api_key,
        }

        body = {
            "q": query,
            "num": research_query.max_results // 2,
            "gl": "us",
            "hl": "en",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session, session.post(
                self._base_url,
                json=body,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    logger.warning("Serper API error: %d", resp.status)
                    return []

                data = await resp.json()
                return self._normalize_results(data.get("organic", []))

        except Exception as e:
            logger.error("Serper search failed: %s", e)
            return []

    def _normalize_results(
        self,
        results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        normalized = []

        for result in results:
            normalized.append({
                "url": result.get("link", ""),
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "position": result.get("position", 0),
            })

        return normalized
