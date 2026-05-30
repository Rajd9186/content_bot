from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from app.research.models import ResearchSource, SourceQuality

logger = logging.getLogger(__name__)


class SourceIngestion:
    def __init__(self) -> None:
        self._ingested_count = 0
        self._duplicate_count = 0
        self._spam_count = 0

    async def ingest(
        self,
        raw_sources: list[dict[str, Any]],
        exclude_domains: list[str] | None = None,
    ) -> list[ResearchSource]:
        ingested = []
        seen_hashes = set()
        seen_urls = set()

        exclude_domains = exclude_domains or []

        for raw in raw_sources:
            try:
                source = self._normalize(raw)

                if source.domain in exclude_domains:
                    continue

                if source.quality == SourceQuality.SPAM:
                    self._spam_count += 1
                    continue

                if self._is_duplicate(source, seen_hashes, seen_urls):
                    self._duplicate_count += 1
                    continue

                ingested.append(source)
                seen_hashes.add(source.content_hash)
                seen_urls.add(source.canonical_url)
                self._ingested_count += 1

            except Exception as e:
                logger.warning("Failed to ingest source: %s", e)

        logger.info(
            "Ingestion complete: %d ingested, %d duplicates, %d spam",
            len(ingested), self._duplicate_count, self._spam_count
        )

        return ingested

    def _normalize(self, raw: dict[str, Any]) -> ResearchSource:
        from urllib.parse import urlparse

        url = raw.get("url", "")
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        canonical = f"{parsed.scheme}://{domain}{parsed.path.rstrip('/')}"

        title = raw.get("title", "Untitled")[:200]
        snippet = raw.get("snippet", "")[:500]

        content_hash = hashlib.sha256(
            f"{title}:{snippet}:{canonical}".encode()
        ).hexdigest()[:16]

        authors = self._extract_authors(raw)
        published_date = self._extract_date(raw)
        source_type = self._classify_type(domain, raw)
        quality = self._assess_quality(domain, raw, title, snippet)

        return ResearchSource(
            url=url,
            canonical_url=canonical,
            domain=domain,
            title=title,
            snippet=snippet,
            content=raw.get("content"),
            authors=authors,
            published_date=published_date,
            source_type=source_type,
            quality=quality,
            metadata={k: v for k, v in raw.items() if k not in [
                "url", "title", "snippet", "content", "authors", "published_date"
            ]},
            content_hash=content_hash,
        )

    def _extract_authors(self, raw: dict[str, Any]) -> list[str]:
        authors = raw.get("authors", [])
        if isinstance(authors, str):
            return [a.strip() for a in authors.split(",") if a.strip()]
        return authors or []

    def _extract_date(self, raw: dict[str, Any]) -> datetime | None:
        date_val = raw.get("published_date")
        if not date_val:
            return None

        if isinstance(date_val, datetime):
            return date_val

        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%B %d, %Y",
            "%d %B %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_val, fmt).replace(tzinfo=UTC)
            except ValueError:
                continue

        return None

    def _classify_type(self, domain: str, raw: dict[str, Any]) -> str:
        academic = [
            "arxiv.org", "scholar.google", "researchgate.net", "academia.edu",
            "ieee.org", "nature.com", "science.org",
        ]
        news = [
            "reuters.com", "bloomberg.com", "cnn.com", "bbc.com",
            "nytimes.com", "wsj.com", "theguardian.com",
        ]
        blog_indicators = ["blog.", "medium.com", "substack.com", "wordpress.com"]

        if any(ad in domain for ad in academic):
            return "academic"
        if any(nd in domain for nd in news):
            return "news"
        if any(bi in domain for bi in blog_indicators):
            return "blog"
        if "stackexchange" in domain or "reddit.com" in domain or "quora.com" in domain:
            return "forum"

        return "web"

    def _assess_quality(
        self,
        domain: str,
        raw: dict[str, Any],
        title: str,
        snippet: str,
    ) -> str:
        high_authority = [
            "arxiv.org", "nature.com", "science.org", "ieee.org", "acm.org",
            "reuters.com", "bloomberg.com", "nytimes.com", "wsj.com", "theguardian.com",
            "wikipedia.org", "github.com", "stackoverflow.com", "docs.python.org",
        ]

        spam_words = ["clickbait", "viral", "shocking", "miracle", "unbelievable", "you won't believe"]

        if any(ha in domain for ha in high_authority):
            return "high"

        title_lower = title.lower()
        snippet_lower = snippet.lower()

        if any(sw in title_lower or sw in snippet_lower for sw in spam_words):
            return "spam"

        authors = raw.get("authors", [])
        published = raw.get("published_date")

        if authors and published:
            return "high"

        if len(snippet) > 150 and len(title) > 10:
            return "medium"

        return "low"

    def _is_duplicate(
        self,
        source: ResearchSource,
        seen_hashes: set[str],
        seen_urls: set[str],
    ) -> bool:
        if source.content_hash in seen_hashes:
            return True
        if source.canonical_url in seen_urls:
            return True

        for existing_hash in seen_hashes:
            if source.content_hash and existing_hash and \
               source.content_hash[:8] == existing_hash[:8]:
                return True

        return False

    def get_stats(self) -> dict[str, int]:
        return {
            "ingested": self._ingested_count,
            "duplicates": self._duplicate_count,
            "spam": self._spam_count,
        }


source_ingestion = SourceIngestion()
