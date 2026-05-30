from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.research.models import ResearchSource

logger = logging.getLogger(__name__)


class RelevanceEngine:
    def __init__(self) -> None:
        self._weights = {
            "semantic": 0.35,
            "keyword": 0.25,
            "recency": 0.20,
            "authority": 0.20,
        }

    def score_all(
        self,
        sources: list[ResearchSource],
        query: str,
        keywords: Optional[list[str]] = None,
    ) -> list[ResearchSource]:
        keywords = keywords or self._extract_keywords(query)
        
        for source in sources:
            source.semantic_score = self._score_semantic(source, query)
            source.keyword_score = self._score_keywords(source, keywords)
            source.recency_score = self._score_recency(source)
            source.authority_score = self._score_authority(source)
            
            source.combined_score = (
                source.semantic_score * self._weights["semantic"] +
                source.keyword_score * self._weights["keyword"] +
                source.recency_score * self._weights["recency"] +
                source.authority_score * self._weights["authority"]
            )
        
        return sorted(sources, key=lambda s: s.combined_score, reverse=True)

    def _extract_keywords(self, query: str) -> list[str]:
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "shall", "can", "need",
            "what", "which", "who", "whom", "whose", "where", "when", "why", "how",
        }
        
        words = query.lower().split()
        keywords = [
            w.strip(".,!?;:\"'()[]{}") for w in words
            if w.lower() not in stop_words and len(w) > 2
        ]
        
        return list(set(keywords))[:10]

    def _score_semantic(self, source: ResearchSource, query: str) -> float:
        query_lower = query.lower()
        title_lower = source.title.lower()
        snippet_lower = source.snippet.lower()
        
        score = 0.0
        
        if query_lower in title_lower:
            score += 0.5
        
        title_words = set(title_lower.split())
        query_words = set(query_lower.split())
        overlap = len(title_words & query_words)
        if overlap > 0:
            score += min(0.3, overlap * 0.05)
        
        if query_lower in snippet_lower:
            score += 0.2
        
        snippet_words = set(snippet_lower.split())
        overlap = len(snippet_words & query_words)
        if overlap > 0:
            score += min(0.2, overlap * 0.02)
        
        return min(1.0, score)

    def _score_keywords(self, source: ResearchSource, keywords: list[str]) -> float:
        if not keywords:
            return 0.0
        
        title_lower = source.title.lower()
        snippet_lower = source.snippet.lower()
        text = f"{title_lower} {snippet_lower}"
        
        matches = sum(1 for kw in keywords if kw in text)
        ratio = matches / len(keywords) if keywords else 0.0
        
        return min(1.0, ratio)

    def _score_recency(self, source: ResearchSource) -> float:
        if not source.published_date:
            return 0.3
        
        now = datetime.now(timezone.utc)
        days_old = (now - source.published_date).days
        
        if days_old <= 7:
            return 1.0
        elif days_old <= 30:
            return 0.8
        elif days_old <= 90:
            return 0.6
        elif days_old <= 365:
            return 0.4
        else:
            return 0.2

    def _score_authority(self, source: ResearchSource) -> float:
        if source.quality == "high":
            base_score = 0.8
        elif source.quality == "medium":
            base_score = 0.5
        else:
            base_score = 0.2
        
        authority_domains = [
            "arxiv.org", "nature.com", "science.org", "ieee.org",
            "reuters.com", "bloomberg.com", "nytimes.com",
            "wikipedia.org", "github.com",
        ]
        
        if any(ad in source.domain for ad in authority_domains):
            base_score = min(1.0, base_score + 0.2)
        
        if source.authors:
            base_score = min(1.0, base_score + 0.1)
        
        if source.published_date:
            base_score = min(1.0, base_score + 0.05)
        
        return base_score

    def filter_by_threshold(
        self,
        sources: list[ResearchSource],
        min_score: float = 0.3,
    ) -> list[ResearchSource]:
        return [s for s in sources if s.combined_score >= min_score]

    def get_top_sources(
        self,
        sources: list[ResearchSource],
        limit: int = 10,
    ) -> list[ResearchSource]:
        return sources[:limit]


relevance_engine = RelevanceEngine()