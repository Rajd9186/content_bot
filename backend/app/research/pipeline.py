from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from typing import Any
from urllib.parse import urlparse

from app.research.models import (
    ResearchQuery,
    ResearchResult,
    ResearchSource,
    SourceQuality,
    SourceType,
)
from app.research.providers.base import BaseSearchProvider
from app.research.providers.factory import SearchProviderFactory

logger = logging.getLogger(__name__)


class ResearchPipeline:
    def __init__(self) -> None:
        self._provider_factory = SearchProviderFactory()
        self._providers: list[BaseSearchProvider] = []
        self._max_parallel = 5
        self._timeout_seconds = 30

    def register_provider(self, provider: BaseSearchProvider) -> None:
        self._providers.append(provider)
        logger.info("Registered search provider: %s", provider.name)

    async def execute(
        self,
        query: ResearchQuery,
        correlation_id: str | None = None,
    ) -> ResearchResult:
        start_time = time.monotonic()
        logger.info("Starting research pipeline for: %s", query.query)

        expanded_queries = await self._expand_queries(query)
        logger.info("Expanded to %d queries", len(expanded_queries))

        search_start = time.monotonic()
        raw_sources = await self._search_all(expanded_queries, query)
        search_latency = (time.monotonic() - search_start) * 1000
        logger.info("Search completed: %d sources in %.0fms", len(raw_sources), search_latency)

        ingestion_start = time.monotonic()
        ingested_sources = await self._ingest_sources(raw_sources, query)
        ingestion_latency = (time.monotonic() - ingestion_start) * 1000
        logger.info("Ingestion completed: %d sources", len(ingested_sources))

        deduplicated = self._deduplicate(ingested_sources)
        logger.info("After deduplication: %d unique sources", len(deduplicated))

        high_quality = [s for s in deduplicated if s.quality != SourceQuality.SPAM]
        total_high_quality = len([s for s in high_quality if s.quality == SourceQuality.HIGH])

        result = ResearchResult(
            query=query.query,
            sources=high_quality[:query.max_results],
            total_found=len(raw_sources),
            total_ingested=len(ingested_sources),
            total_after_dedup=len(deduplicated),
            total_high_quality=total_high_quality,
            search_latency_ms=search_latency,
            ingestion_latency_ms=ingestion_latency,
        )

        logger.info(
            "Research pipeline complete: %d sources (%d high quality) in %.0fms",
            len(result.sources), total_high_quality,
            (time.monotonic() - start_time) * 1000
        )

        return result

    async def _expand_queries(self, query: ResearchQuery) -> list[str]:
        expanded = [query.query]

        topic_expansions = []
        for topic in query.topics:
            topic_expansions.extend([
                f"{query.query} {topic}",
                f"{topic} {query.query} best practices",
                f"{query.query} in {topic}",
            ])

        query_expansions = [
            f"{query.query} 2025 2026",
            f"{query.query} guide tutorial",
            f"{query.query} research study",
            f"what is {query.query}",
            f"{query.query} benefits challenges",
        ]

        expanded.extend(topic_expansions[:5])
        expanded.extend(query_expansions)

        if query.expanded_queries:
            expanded.extend(query.expanded_queries)

        seen = set()
        unique = []
        for q in expanded:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique.append(q)

        return unique[:15]

    async def _search_all(
        self,
        queries: list[str],
        query: ResearchQuery,
    ) -> list[dict[str, Any]]:
        if not self._providers:
            logger.warning("No search providers registered, using mock provider")
            from app.research.providers.mock import MockSearchProvider
            mock = MockSearchProvider()
            self.register_provider(mock)

        semaphore = asyncio.Semaphore(self._max_parallel)

        async def search_with_semaphore(provider: BaseSearchProvider, q: str) -> list[dict[str, Any]]:
            async with semaphore:
                try:
                    return await asyncio.wait_for(
                        provider.search(q, query),
                        timeout=self._timeout_seconds
                    )
                except TimeoutError:
                    logger.warning("Search timeout for query: %s", q)
                    return []
                except Exception as e:
                    logger.warning("Search error for %s: %s", q, e)
                    return []

        tasks = []
        for provider in self._providers:
            for q in queries[:3]:
                tasks.append(search_with_semaphore(provider, q))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_results = []
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)

        return all_results

    async def _ingest_sources(
        self,
        raw_sources: list[dict[str, Any]],
        query: ResearchQuery,
    ) -> list[ResearchSource]:
        ingested = []
        for raw in raw_sources:
            try:
                source = self._normalize_source(raw, query)
                if self._passes_filters(source, query):
                    ingested.append(source)
            except Exception as e:
                logger.warning("Failed to ingest source: %s", e)

        return ingested

    def _normalize_source(
        self,
        raw: dict[str, Any],
        query: ResearchQuery,
    ) -> ResearchSource:
        url = raw.get("url", "")
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        canonical = f"{parsed.scheme}://{domain}{parsed.path.rstrip('/')}"

        content_hash = hashlib.sha256(
            f"{raw.get('title', '')}:{raw.get('snippet', '')}:{url}".encode()
        ).hexdigest()[:16]

        source_type = self._classify_source_type(domain, raw)
        quality = self._assess_quality(domain, raw)

        return ResearchSource(
            url=url,
            canonical_url=canonical,
            domain=domain,
            title=raw.get("title", "Untitled")[:200],
            snippet=raw.get("snippet", "")[:500],
            content=raw.get("content"),
            authors=raw.get("authors", []),
            published_date=raw.get("published_date"),
            source_type=source_type,
            quality=quality,
            metadata={k: v for k, v in raw.items() if k not in ["url", "title", "snippet"]},
            content_hash=content_hash,
        )

    def _classify_source_type(
        self,
        domain: str,
        raw: dict[str, Any],
    ) -> SourceType:
        academic_domains = ["arxiv.org", "scholar.google", "researchgate", "academia.edu"]
        news_domains = ["reuters", "bloomberg", "cnn", "bbc", "nytimes", "wsj"]
        blog_indicators = ["blog", "medium", "substack", "wordpress"]

        if any(ad in domain for ad in academic_domains):
            return SourceType.ACADEMIC
        if any(nd in domain for nd in news_domains):
            return SourceType.NEWS
        if any(bi in domain for bi in blog_indicators):
            return SourceType.BLOG
        if "stackexchange" in domain or "reddit" in domain or "quora" in domain:
            return SourceType.FORUM

        return SourceType.WEB

    def _assess_quality(
        self,
        domain: str,
        raw: dict[str, Any],
    ) -> SourceQuality:
        high_authority = [
            "arxiv.org", "nature.com", "science.org", "ieee.org",
            "reuters.com", "bloomberg.com", "nytimes.com", "wsj.com",
            "wikipedia.org", "github.com", "stackoverflow.com",
        ]

        spam_indicators = ["clickbait", "viral", "shocking", "miracle"]

        if any(ha in domain for ha in high_authority):
            return SourceQuality.HIGH

        title = raw.get("title", "").lower()
        snippet = raw.get("snippet", "").lower()

        if any(si in title or si in snippet for si in spam_indicators):
            return SourceQuality.SPAM

        if raw.get("authors") and raw.get("published_date"):
            return SourceQuality.HIGH

        if len(raw.get("snippet", "")) > 100:
            return SourceQuality.MEDIUM

        return SourceQuality.LOW

    def _passes_filters(
        self,
        source: ResearchSource,
        query: ResearchQuery,
    ) -> bool:
        if query.domains and source.domain not in query.domains:
            return False

        if source.domain in query.exclude_domains:
            return False

        if source.quality == SourceQuality.SPAM:
            return False

        quality_order = {
            SourceQuality.HIGH: 3,
            SourceQuality.MEDIUM: 2,
            SourceQuality.LOW: 1,
            SourceQuality.SPAM: 0,
        }

        return not quality_order[source.quality] < quality_order[query.min_quality]

    def _deduplicate(
        self,
        sources: list[ResearchSource],
    ) -> list[ResearchSource]:
        seen_hashes = set()
        seen_urls = set()
        deduplicated = []

        for source in sources:
            if source.content_hash and source.content_hash in seen_hashes:
                continue
            if source.canonical_url in seen_urls:
                continue

            seen_hashes.add(source.content_hash)
            seen_urls.add(source.canonical_url)
            deduplicated.append(source)

        return sorted(deduplicated, key=lambda s: s.combined_score, reverse=True)


research_pipeline = ResearchPipeline()
