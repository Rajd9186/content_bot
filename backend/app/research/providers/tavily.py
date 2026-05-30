from __future__ import annotations

import logging
import os
from typing import Any

import aiohttp

from app.research.models import ResearchQuery
from app.research.providers.base import BaseSearchProvider

logger = logging.getLogger(__name__)


class TavilyProvider(BaseSearchProvider):
    def __init__(self) -> None:
        super().__init__("tavily")
        self._api_key = os.getenv("TAVILY_API_KEY", "")
        self._base_url = "https://api.tavily.com/search"

    async def search(
        self,
        query: str,
        research_query: ResearchQuery,
    ) -> list[dict[str, Any]]:
        if not self._api_key:
            logger.warning("Tavily API key not configured")
            return []
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }
        
        body = {
            "query": query,
            "search_depth": "advanced",
            "include_answer": False,
            "include_raw_content": True,
            "max_results": research_query.max_results // 2,
            "include_domains": research_query.domains or [],
            "exclude_domains": research_query.exclude_domains or [],
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self._base_url,
                    json=body,
                    headers=headers
                ) as resp:
                    if resp.status != 200:
                        logger.warning("Tavily API error: %d", resp.status)
                        return []
                    
                    data = await resp.json()
                    return self._normalize_results(data.get("results", []))
        
        except Exception as e:
            logger.error("Tavily search failed: %s", e)
            return []

    def _normalize_results(
        self,
        results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        normalized = []
        
        for result in results:
            normalized.append({
                "url": result.get("url", ""),
                "title": result.get("title", ""),
                "snippet": result.get("content", ""),
                "content": result.get("raw_content", ""),
                "score": result.get("score", 0.0),
                "published_date": result.get("published_date"),
            })
        
        return normalized