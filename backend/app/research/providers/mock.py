from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from app.research.models import ResearchQuery
from app.research.providers.base import BaseSearchProvider

logger = logging.getLogger(__name__)


class MockSearchProvider(BaseSearchProvider):
    """Mock provider for testing and development"""
    
    def __init__(self) -> None:
        super().__init__("mock")

    async def search(
        self,
        query: str,
        research_query: ResearchQuery,
    ) -> list[dict[str, Any]]:
        logger.info("Mock search for: %s", query)
        
        mock_results = [
            {
                "url": f"https://example.com/article-{i}",
                "title": f"Comprehensive Guide to {query} - Part {i}",
                "snippet": self._generate_snippet(query, i),
                "content": self._generate_content(query, i),
                "authors": [f"Author {i}"],
                "published_date": datetime.now(timezone.utc) - timedelta(days=i*5),
                "domain": "example.com",
                "source_type": "web",
            }
            for i in range(1, 8)
        ]
        
        academic_result = {
            "url": f"https://arxiv.org/abs/2024.{query.replace(' ', '')}",
            "title": f"Research Study on {query}: A Comprehensive Analysis",
            "snippet": f"Peer-reviewed research examining {query} in depth with statistical analysis and expert commentary.",
            "content": f"Full academic paper on {query}",
            "authors": ["Dr. Researcher", "Prof. Expert"],
            "published_date": datetime.now(timezone.utc) - timedelta(days=30),
            "domain": "arxiv.org",
            "source_type": "academic",
        }
        
        mock_results.append(academic_result)
        
        news_result = {
            "url": "https://reuters.com/technology/latest",
            "title": f"Breaking: New Developments in {query}",
            "snippet": f"Industry leaders announce major breakthroughs related to {query}, marking significant progress.",
            "content": "Full news article",
            "authors": ["News Team"],
            "published_date": datetime.now(timezone.utc) - timedelta(days=2),
            "domain": "reuters.com",
            "source_type": "news",
        }
        
        mock_results.append(news_result)
        
        return mock_results

    def _generate_snippet(self, query: str, i: int) -> str:
        return (
            f"This comprehensive resource explores {query} in detail, "
            f"covering key concepts, best practices, and real-world applications. "
            f"Part {i} of our series provides actionable insights and expert analysis "
            f"to help you understand the fundamentals and advanced topics."
        )

    def _generate_content(self, query: str, i: int) -> str:
        return (
            f"# {query} - Part {i}\n\n"
            f"## Introduction\n\n"
            f"{query} represents a significant area of interest and development. "
            f"This article provides comprehensive coverage of the topic.\n\n"
            f"## Key Points\n\n"
            f"1. Fundamental concepts and definitions\n"
            f"2. Practical applications and use cases\n"
            f"3. Best practices and recommendations\n"
            f"4. Future trends and developments\n\n"
            f"## Conclusion\n\n"
            f"Understanding {query} is essential for success in this field."
        )